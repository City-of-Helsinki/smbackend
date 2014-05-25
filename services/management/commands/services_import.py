# -*- coding: utf-8 -*-

import sys
import re
import json
from datetime import datetime
from optparse import make_option
import logging
import hashlib
from pprint import pprint

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

    importer_types = ['organizations', 'departments', 'services', 'units']
    supported_languages = ['fi', 'sv', 'en']

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            method = "import_%s" % imp
            assert getattr(self, method, False), "No importer defined for %s" % method
            opt = make_option('--%s' % imp, dest=imp, action='store_true', help='import %s' % imp)
            self.option_list.append(opt)
        self.services = {}

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

    def _save_translated_field(self, obj, obj_field_name, info, info_field_name, max_length=None):
        args = {}
        for lang in ('fi', 'sv', 'en'):
            key = '%s_%s' % (info_field_name, lang)
            if key in info:
                val = self.clean_text(info[key])
            else:
                val = None
            if max_length and val and len(val) > max_length:
                self.logger.warning("%s: field '%s' too long" % (obj, obj_field_name))
                val = None
            obj_key = '%s_%s' % (obj_field_name, lang)
            obj_val = getattr(obj, obj_key, None)
            if obj_val == val:
                continue

            setattr(obj, obj_key, val)
            if lang == 'fi':
                setattr(obj, obj_field_name, val)
            obj._changed = True

    def _set_field(self, obj, field_name, val):
        if not hasattr(obj, field_name):
            print(vars(obj))
        obj_val = getattr(obj, field_name)
        if obj_val == val:
            return
        setattr(obj, field_name, val)
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

    def mark_service_depths(self, service_dict, srv, level):
        srv['level'] = level
        if not 'child_ids' in srv:
            return
        for child_id in srv['child_ids']:
            child = service_dict[child_id]
            self.mark_service_depths(service_dict, child, level + 1)

    def detect_duplicate_services(self, service_list):
        service_dict = {srv['id']: srv for srv in service_list}
        # Mark the tree depth for each service for later sorting starting
        # from root nodes.
        for srv in service_list:
            if not 'parent_id' in srv:
                self.mark_service_depths(service_dict, srv, 0)
            srv['units'] = []
            srv['child_ids_dupes'] = srv['child_ids']

        unit_list = self._fetch_units()

        for unit in unit_list:
            service_ids = sorted(unit.get('service_ids', []))
            # Make note of what units supply each service. If the unit sets
            # and names for services match, we treat them as identical.
            for srv_id in service_ids:
                srv = service_dict[srv_id]
                srv['units'].append(unit['id'])

        srv_by_name = {}
        for srv in service_list:
            name = srv['name_fi'].lower()
            if name not in srv_by_name:
                srv_by_name[name] = []
            srv_by_name[name].append(srv)

        count = 0
        # Go through the list starting from the leaves.
        for srv in sorted(service_list, key=lambda x: (-x['level'], x['id'])):
            srv['duplicates'] = []
            if 'identical_to' in srv:
                continue
            duplicate_names = srv_by_name[srv['name_fi'].lower()]
            if len(duplicate_names) < 2:
                continue
            for srv2 in duplicate_names:
                if srv2 == srv:
                    continue
                un1 = sorted(srv['units'])
                un2 = sorted(srv2['units'])
                if un1 != un2:
                    continue
                ch1 = sorted(srv['child_ids_dupes'])
                ch2 = sorted(srv2['child_ids_dupes'])
                if ch1 != ch2:
                    continue
                srv['duplicates'].append(srv2['id'])
                srv2['identical_to'] = srv['id']
                if 'parent_id' in srv2:
                    # Replace the ID of the child with the ID of the duplicate
                    parent = service_dict[srv2['parent_id']]
                    parent['child_ids_dupes'] = [srv['id'] if x == srv2['id'] else x for x in parent['child_ids_dupes']]
                count += 1

        self.logger.info("Found %d duplicate services" % count)

    @db.transaction.atomic
    def import_services(self):
        srv_list = self.pk_get('service')
        syncher = ModelSyncher(Service.objects.all(), lambda obj: obj.id)

        self.detect_duplicate_services(srv_list)

        dupes = []
        for d in srv_list:
            obj = syncher.get(d['id'])
            if not obj:
                obj = Service(id=d['id'])
                obj._changed = True
            self._save_translated_field(obj, 'name', d, 'name')

            if 'identical_to' in d:
                master = syncher.get(d['identical_to'])
                # If the master entry hasn't been saved yet, we save the
                # duplicate information later.
                if not master:
                    dupes.append((obj, d['identical_to']))
                    d['identical_to'] = None
            else:
                d['identical_to'] = None

            self._set_field(obj, 'identical_to_id', d['identical_to'])

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

        for obj, master_id in dupes:
            obj.identical_to_id = master_id
            obj.save(update_fields=['identical_to'])

        syncher.finish()

    def _save_searchwords(self, obj, info, language):
        field_name = 'extra_searchwords_%s' % language
        if not field_name in info:
            new_kw_set = set()
        else:
            kws = [x.strip() for x in info[field_name].split(',')]
            kws = [x for x in kws if x]
            new_kw_set = set()
            for kw in kws:
                if not kw in self.keywords[language]:
                    kw_obj = Keyword(name=kw, language=language)
                    kw_obj.save()
                    self.keywords[language][kw] = kw_obj
                    self.keywords_by_id[kw_obj.pk] = kw_obj
                else:
                    kw_obj = self.keywords[language][kw]
                new_kw_set.add(kw_obj.pk)

        obj.new_keywords |= new_kw_set

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
            obj._changed = False
            obj.save()


        service_ids = sorted(info.get('service_ids', []))
        obj_service_ids = sorted(obj.services.values_list('id', flat=True))
        if obj_service_ids != service_ids:
            if not obj._created:
                print("%s service set changed: %s -> %s" % (obj, obj_service_ids, service_ids))
            obj.services = service_ids
            obj._changed = True


        obj.new_keywords = set()
        for lang in self.supported_languages:
            self._save_searchwords(obj, info, lang)

        old_kw_set = set(obj.keywords.all().values_list('pk', flat=True))
        if old_kw_set != obj.new_keywords:
            old_kw_str = ', '.join([self.keywords_by_id[x].name for x in old_kw_set])
            new_kw_str = ', '.join([self.keywords_by_id[x].name for x in obj.new_keywords])
            print("%s keyword set changed: %s -> %s" % (obj, old_kw_str, new_kw_str))
            obj.keywords = list(obj.new_keywords)
            obj._changed = True


        if info['connections']:
            conn_json = json.dumps(info['connections'], ensure_ascii=False, sort_keys=True).encode('utf8')
            conn_hash = hashlib.sha1(conn_json).hexdigest()
        else:
            conn_hash = None

        if obj.connection_hash != conn_hash:
            self.logger.info("%s connection set changed (%s vs. %s)" % (obj, obj.connection_hash, conn_hash))
            obj.connections.all().delete()
            for conn in info['connections']:
                c = UnitConnection(unit=obj)
                self._save_translated_field(c, 'name', conn, 'name', max_length=400)
                self._save_translated_field(c, 'www_url', conn, 'www')
                c.section = conn['section_type'].lower()
                c.type = int(conn['connection_type'])
                fields = ['contact_person', 'email', 'phone', 'phone_mobile']
                for field in fields:
                    val = info.get(field, None)
                    if getattr(c, field) != val:
                        setattr(c, field, val)
                        c._changed = True
                c.save()
            obj.connection_hash = conn_hash
            obj.save(update_fields=['connection_hash'])


        """
        conn_by_type = {}
        for conn in info['connections']:
            conn_type = key_from_conn(conn)
            if conn_type not in conn_by_type:
                conn_by_type[conn_type] = {}
            d = conn_by_type[conn_type]
            for key, val in conn.items():
                if key in d:
                    if d[key] != val:
                        self.logger.warning("%s: conflict in connections (%s vs. %s)" % (obj, d[key], val))
                else:
                    d[key] = val
        """

        if obj._changed:
            obj.origin_last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save(update_fields=['origin_last_modified_time'])

        syncher.mark(obj)

    def _fetch_units(self):
        if hasattr(self, 'unit_list'):
            return self.unit_list
        self.logger.info("Fetching units")
        obj_list = self.pk_get('unit')
        self.unit_list = obj_list
        return obj_list

    def import_units(self):
        self.keywords = {}
        for lang in self.supported_languages:
            kw_list = Keyword.objects.filter(language=lang)
            kw_dict = {kw.name: kw for kw in kw_list}
            self.keywords[lang] = kw_dict
        self.keywords_by_id = {kw.pk: kw for kw in Keyword.objects.all()}

        if not getattr(self, 'org_syncher', None):
            self.import_organizations(noop=True)
        if not getattr(self, 'dept_syncher', None):
            self.import_departments(noop=True)

        if self.options['single']:
            obj_id = self.options['single']
            obj_list = [self.pk_get('unit', obj_id)]
            queryset = Unit.objects.filter(id=obj_id)
        else:
            obj_list = self._fetch_units()
            queryset = Unit.objects.all().select_related('services', 'keywords')

        self.logger.info("Fetching unit connections")
        if self.options['single']:
            connections = [self.pk_get('connection', obj_id)]
        else:
            connections = self.pk_get('connection')
        conn_by_unit = {}
        for conn in connections:
            unit_id = conn['unit_id']
            if unit_id not in conn_by_unit:
                conn_by_unit[unit_id] = []
            conn_by_unit[unit_id].append(conn)

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
            conn_list = conn_by_unit.get(info['id'], [])
            info['connections'] = conn_list
            self._import_unit(syncher, info)
        syncher.finish()

    def handle(self, **options):
        self.options = options
        self.org_syncher = None
        self.dept_syncher = None
        self.logger = logging.getLogger(__name__)

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
