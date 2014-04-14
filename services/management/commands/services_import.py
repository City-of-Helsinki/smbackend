# -*- coding: utf-8 -*-

import sys
import re
from datetime import datetime
from optparse import make_option

import requests
import requests_cache
import pytz
from django.core.management.base import BaseCommand
from django import db
from django.conf import settings
from django.db import transaction
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.utils.translation import activate, get_language

from munigeo.models import *
from munigeo.importer.sync import ModelSyncher
from services.models import *

URL_BASE = 'http://www.hel.fi/palvelukarttaws/rest/v3/'
GK25_SRID = 3879

UTC_TIMEZONE = pytz.timezone('UTC')

class Command(BaseCommand):
    help = "Import services from Palvelukartta REST API"
    option_list = list(BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--single', dest='single', action='store', metavar='ID', type='string', help='import only single entity'),
    ))

    importer_types = ['organizations', 'departments', 'units', 'services']

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            method = "import_%s" % imp
            assert getattr(self, method, False), "No importer defined for %s" % method
            opt = make_option('--%s' % imp, dest=imp, action='store_true', help='import %s' % imp)
            self.option_list.append(opt)

    def clean_text(self, text):
        #text = text.replace('\n', ' ')
        #text = text.replace(u'\u00a0', ' ')
        # remove consecutive whitespaces
        text = re.sub(r'\s\s+', ' ', text, re.U)
        # remove nil bytes
        text = text.replace('\u0000', ' ')
        text = text.strip()
        return text

    def pk_get(self, resource_name, res_id=None):
        url = "%s%s/" % (URL_BASE, resource_name)
        if res_id != None:
            url = "%s%s/" % (url, res_id)
        resp = requests.get(url)
        assert resp.status_code == 200
        return resp.json()

    def _save_translated_field(self, obj, obj_field_name, info, info_field_name):
        args = {}
        for lang in ('fi', 'sv', 'en'):
            key = '%s_%s' % (info_field_name, lang)
            if key in info:
                val = self.clean_text(info[key])
            else:
                val = None
            obj_key = '%s_%s' % (obj_field_name, lang)
            obj_val = getattr(obj, obj_key, None)
            if obj_val == val:
                continue

            setattr(obj, obj_key, val)
            if lang == 'fi':
                setattr(obj, obj_field_name, val)
            obj._changed = True

    @db.transaction.atomic
    def import_organizations(self, noop=False):
        obj_list = self.pk_get('organization')
        syncher = ModelSyncher(Organization.objects.all(), lambda obj: obj.id)
        self.org_syncher = syncher
        if noop:
            return

        for d in obj_list:
            obj = syncher.get(d['id'])
            if not obj:
                obj = Organization(id=d['id'])
            self._save_translated_field(obj, 'name', d, 'name')

            url = d['data_source_url']
            if not url.startswith('http'):
                url = 'http://%s' % url
            if obj.data_source_url != url:
                obj._changed = True
                obj.data_source_url = url

            if obj._changed:
                obj.save()
            syncher.mark(obj)

        syncher.finish()

    @db.transaction.atomic
    def import_departments(self, noop=False):
        obj_list = self.pk_get('department')
        syncher = ModelSyncher(Department.objects.all(), lambda obj: obj.id)
        self.dept_syncher = syncher
        if noop:
            return

        for d in obj_list:
            obj = syncher.get(d['id'])
            if not obj:
                obj = Department(id=d['id'])
                obj._changed = True
            self._save_translated_field(obj, 'name', d, 'name')
            if obj.abbr != d['abbr']:
                obj._changed = True
                obj.abbr = d['abbr']

            if self.org_syncher:
                org_obj = self.org_syncher.get(d['org_id'])
            else:
                org_obj = Organization.objects.get(id=d['org_id'])
            assert org_obj
            if obj.organization_id != d['org_id']:
                obj._changed = True
                obj.organization = org_obj

            if obj._changed:
                obj.save()
            syncher.mark(obj)

        syncher.finish()

    @db.transaction.atomic
    def import_services(self):
        obj_list = self.pk_get('service')
        syncher = ModelSyncher(Service.objects.all(), lambda obj: obj.id)

        for d in obj_list:
            obj = syncher.get(d['id'])
            if not obj:
                obj = Service(id=d['id'])
                obj._changed = True
            self._save_translated_field(obj, 'name', d, 'name')

            if 'parent_id' in d:
                parent = syncher.get(d['parent_id'])
                assert parent
            else:
                parent = None
            if obj.parent != parent:
                obj.parent = parent
                obj._changed = True

            if obj._changed:
                obj.save()
            syncher.mark(obj)
        syncher.finish()

    @db.transaction.atomic
    def _import_unit(self, syncher, info):
        obj = syncher.get(info['id'])
        if not obj:
            obj = Unit(id=info['id'])
            obj._changed = True
            obj._created = True
        else:
            obj._created = False

        self._save_translated_field(obj, 'name', info, 'name')
        self._save_translated_field(obj, 'description', info, 'desc')
        self._save_translated_field(obj, 'street_address', info, 'street_address')

        self._save_translated_field(obj, 'www_url', info, 'www')
        self._save_translated_field(obj, 'picture_caption', info, 'picture_caption')

        org_id = info['org_id']
        if self.org_syncher:
            org = self.org_syncher.get(info['org_id'])
        else:
            org = Organization.objects.get(id=info['org_id'])
        assert org != None
        if obj.organization_id != org_id:
            obj.organization = org
            obj._changed = True

        if 'dept_id' in info:
            new_dept = None
            if info['dept_id'] == 'TASKE':
                print("Overriding department for %s" % info['name_fi'])
                info['dept_id'] = 'KANSLIA'
            elif info['dept_id'] in ('1008-NOBIL', '1009-ULK'):
                print("Removing %s dept from %s" % (info['dept_id'], info['name_fi']))
                del info['dept_id']

        if 'dept_id' in info:
            dept_id = info['dept_id']
            if self.dept_syncher:
                dept = self.dept_syncher.get(dept_id)
            else:
                try:
                    dept = Department.objects.get(id=dept_id)
                except Department.DoesNotExist:
                    print("Department %s does not exist" % dept_id)
                    raise
            assert dept != None
        else:
            #print("%s does not have department id" % obj)
            dept = None
            dept_id = None
        if obj.department_id != dept_id:
            obj.department = dept
            obj._changed = True

        fields = ['address_zip', 'address_postal_full', 'phone', 'email', 'provider_type', 'picture_url']
        for field in fields:
            val = info.get(field, None)
            if getattr(obj, field) != val:
                setattr(obj, field, val)
                obj._changed = True

        url = info.get('data_source_url', None)
        if url:
            if not url.startswith('http'):
                url = 'http://%s' % url
        if obj.data_source_url != url:
            obj._changed = True
            obj.data_source_url = url

        n = info.get('latitude', 0)
        e = info.get('longitude', 0)
        location = None
        if n and e:
            p = Point(e, n, srid=4326) # GPS coordinate system
            if p.within(self.bounding_box):
                if self.target_srid != 4326:
                    p.transform(self.gps_to_target_ct)
                location = p
            else:
                print("Invalid coordinates (%f, %f) for %s" % (n, e, obj))

        if location and obj.location:
            # If the distance is less than 10cm, assume the location
            # hasn't changed.
            assert obj.location.srid == settings.PROJECTION_SRID
            if location.distance(obj.location) < 0.10:
                location = obj.location
        if location != obj.location:
            obj._changed = True
            obj.location = location

        if obj._changed:
            if obj._created:
                verb = "created"
            else:
                verb = "changed"
            print("%s %s" % (obj, verb))
            obj.origin_last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()

        service_ids = sorted(info.get('service_ids', []))
        obj_service_ids = sorted(obj.services.values_list('id', flat=True))
        if obj_service_ids != service_ids:
            if not obj._created:
                print("%s service set changed: %s -> %s" % (obj, obj_service_ids, service_ids))
            obj.services = service_ids

        syncher.mark(obj)

    def import_units(self):
        if not getattr(self, 'org_syncher', None):
            self.import_organizations(noop=True)
        if not getattr(self, 'dept_syncher', None):
            self.import_departments(noop=True)

        if self.options['single']:
            obj_id = self.options['single']
            obj_list = [self.pk_get('unit', obj_id)]
            queryset = Unit.objects.filter(id=obj_id)
        else:
            obj_list = self.pk_get('unit')
            queryset = Unit.objects.all().select_related('services')

        self.target_srid = settings.PROJECTION_SRID
        self.bounding_box = Polygon.from_bbox(settings.BOUNDING_BOX)
        self.bounding_box.set_srid(4326)
        gps_srs = SpatialReference(4326)
        target_srs = SpatialReference(self.target_srid)
        target_to_gps_ct = CoordTransform(target_srs, gps_srs)
        self.bounding_box.transform(target_to_gps_ct)
        self.gps_to_target_ct = CoordTransform(gps_srs, target_srs)

        syncher = ModelSyncher(queryset, lambda obj: obj.id)
        for idx, info in enumerate(obj_list):
            self._import_unit(syncher, info)
        syncher.finish()

    def handle(self, **options):
        self.options = options
        self.org_syncher = None
        self.dept_syncher = None

        if options['cached']:
            requests_cache.install_cache('services_import')

        # Activate the default language for the duration of the import
        # to make sure translated fields are populated correctly.
        old_lang = get_language()
        activate(settings.LANGUAGES[0][0])

        import_count = 0
        for imp in self.importer_types:
            if not self.options[imp]:
                continue
            method = getattr(self, "import_%s" % imp)
            print("Importing %s..." % imp)
            method()
            import_count += 1
        if not import_count:
            sys.stderr.write("Nothing to import.\n")
        activate(old_lang)
