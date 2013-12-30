# -*- coding: utf-8 -*-

from datetime import datetime

import requests
import requests_cache
from optparse import make_option
from django.core.management.base import BaseCommand
from django import db
from django.conf import settings
from django.db import transaction

from munigeo.models import *
from munigeo.importer.sync import ModelSyncher
from services.models import *

requests_cache.install_cache('services_import')

URL_BASE = 'http://www.hel.fi/palvelukarttaws/rest/v2/'

class Command(BaseCommand):
    help = "Import services from Palvelukartta REST API"
    option_list = BaseCommand.option_list + (
    )

    def clean_text(self, text):
        #text = text.replace('\n', ' ')
        #text = text.replace(u'\u00a0', ' ')
        # remove consecutive whitespaces
        #text = re.sub(r'\s\s+', ' ', text, re.U)
        text = text.strip()
        return text

    def pk_get_list(self, resource_name):
        url = "%s%s/" % (URL_BASE, resource_name)
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
            if getattr(obj, key, None) == val:
                continue
            args['language'] = lang
            args[obj_field_name] = val
            obj.translate(**args)
            obj._changed = True

    def import_organizations(self):
        obj_list = self.pk_get_list('organization')
        syncher = ModelSyncher(Organization.objects.all(), lambda obj: obj.id)

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
        self.org_syncher = syncher

    def import_departments(self):
        obj_list = self.pk_get_list('department')
        syncher = ModelSyncher(Department.objects.all(), lambda obj: obj.id)

        for d in obj_list:
            obj = syncher.get(d['id'])
            if not obj:
                obj = Department(id=d['id'])
                obj._changed = True
            self._save_translated_field(obj, 'name', d, 'name')
            if obj.abbr != d['abbr']:
                obj._changed = True
                obj.abbr = d['abbr']

            org_obj = self.org_syncher.get(d['org_id'])
            assert org_obj
            if obj.organization_id != d['org_id']:
                obj._changed = True
                obj.organization = org_obj

            if obj._changed:
                print("%s changed" % obj)
                obj.save()
            syncher.mark(obj)

        syncher.finish()
        self.dept_syncher = syncher

    def import_services(self):
        obj_list = self.pk_get_list('service')
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

    def import_units(self):
        obj_list = self.pk_get_list('unit')
        syncher = ModelSyncher(Unit.objects.all(), lambda obj: obj.id)

        for d in obj_list:
            obj = syncher.get(d['id'])
            if not obj:
                obj = Unit(id=d['id'])
                obj._changed = True

            self._save_translated_field(obj, 'name', d, 'name')
            self._save_translated_field(obj, 'street_address', d, 'street_address')

            self._save_translated_field(obj, 'www_url', d, 'www')

            if 'dept_id' in d:
                dept_id = d['dept_id']
                dept = self.dept_syncher.get(dept_id)
                assert dept != None
            else:
                #print("%s does not have department id" % obj)
                dept = None
                dept_id = None
            if obj.department_id != dept_id:
                obj.department = dept
                obj._changed = True

            org_id = d['org_id']
            org = self.org_syncher.get(org_id)
            if not org:
                print(d)
            assert org != None
            if obj.organization_id != org_id:
                obj.organization = org
                obj._changed = True

            fields = ['address_zip', 'address_postal_full', 'phone', 'email']
            for field in fields:
                val = d.get(field, None)
                if getattr(obj, field) != val:
                    setattr(obj, field, val)
                    obj._changed = True

            url = d.get('data_source_url', None)
            if url:
                if not url.startswith('http'):
                    url = 'http://%s' % url
            if obj.data_source_url != url:
                obj._changed = True
                obj.data_source_url = url

            if obj._changed:
                print("%s changed" % obj)
                obj.origin_last_modified_time = datetime.now(timezone.get_default_timezone())
                obj.save()
            syncher.mark(obj)

        syncher.finish()

    def handle(self, **options):
        print("Importing organizations...")
        self.import_organizations()
        print("Importing departments...")
        self.import_departments()
        print("Importing services...")
        self.import_services()
        print("Importing units...")
        self.import_units()
