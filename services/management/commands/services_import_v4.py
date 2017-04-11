# -*- coding: utf-8 -*-
import sys
import re
import os
import json
from collections import defaultdict
import csv
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

from munigeo.models import Municipality
from munigeo.importer.sync import ModelSyncher

from services.management.commands.services_import.aliases import import_aliases
from services.management.commands.services_import.departments import import_departments
from services.management.commands.services_import.organizations import import_organizations
from services.management.commands.services_import.services import import_services
from services.management.commands.services_import.units import import_units
from services.management.commands.services_import.accessibility import import_accessibility
from services.models import *
from services.models.unit import PROJECTION_SRID

URL_BASE = 'http://www.hel.fi/palvelukarttaws/rest/v4/'
GK25_SRID = 3879

UTC_TIMEZONE = pytz.timezone('UTC')


class Command(BaseCommand):
    help = "Import services from Palvelukartta REST API"
    option_list = list(BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--single', dest='single', action='store', metavar='ID', type='string', help='import only single entity'),
    ))

    importer_types = ['organizations', 'services', 'units', 'departments', 'aliases', 'accessibility']
    supported_languages = ['fi', 'sv', 'en']

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            method = "import_%s" % imp
            assert getattr(self, method, False), "No importer defined for %s" % method
            opt = make_option('--%s' % imp, dest=imp, action='store_true', help='import %s' % imp)
            self.option_list.append(opt)
        self.services = {}
        self.existing_servicetype_ids = None
        self.existing_servicenode_ids = None


    def clean_text(self, text):
        #text = text.replace('\n', ' ')
        #text = text.replace(u'\u00a0', ' ')
        # remove consecutive whitespaces
        text = re.sub(r'\s\s+', ' ', text, re.U)
        # remove nil bytes
        text = text.replace('\u0000', ' ')
        text = text.strip()
        return text

    def pk_get(self, resource_name, res_id=None, v3=False):
        url = "%s%s/" % (URL_BASE, resource_name)
        if res_id != None:
            url = "%s%s/" % (url, res_id)
        if v3:
            url = url.replace('v4', 'v3')
        resp = requests.get(url)
        assert resp.status_code == 200, 'fuu status code {}'.format(resp.status_code)
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
                if self.verbosity:
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

    def _sync_searchwords(self, obj, info):
        obj.new_keywords = set()
        for lang in self.supported_languages:
            self._save_searchwords(obj, info, lang)

        old_kw_set = set(obj.keywords.all().values_list('pk', flat=True))
        if old_kw_set == obj.new_keywords:
            return

        if self.verbosity:
            old_kw_str = ', '.join([self.keywords_by_id[x].name for x in old_kw_set])
            new_kw_str = ', '.join([self.keywords_by_id[x].name for x in obj.new_keywords])
            print("%s keyword set changed: %s -> %s" % (obj, old_kw_str, new_kw_str))
        obj.keywords = list(obj.new_keywords)
        obj._changed = True


    @db.transaction.atomic
    def import_organizations(self, noop=False):
        return import_organizations(logger=self.logger, noop=noop, org_syncher=self.org_syncher)


    @db.transaction.atomic
    def import_departments(self, noop=False):
        import_departments(logger=self.logger, noop=noop, org_syncher=self.org_syncher)

    def import_aliases(self):
        import_aliases()

    @db.transaction.atomic
    def import_accessibility(self, noop=False):
        import_accessibility(logger=self.logger, noop=noop)

    # def _fetch_units(self):
    #     if hasattr(self, 'unit_list'):
    #         return self.unit_list
    #     if self.verbosity:
    #         self.logger.info("Fetching units")
    #     obj_list = self.pk_get('unit')
    #     self.unit_list = obj_list
    #     return obj_list

    def _fetch_unit_accessibility_properties(self, unit_pk):
        if self.verbosity:
            self.logger.info("Fetching unit accessibility "
                             "properties for unit {}".format(unit_pk))
        obj_list = self.pk_get('unit/{}/accessibility'.format(unit_pk))
        return obj_list

    def import_units(self):
        import_units()

    @db.transaction.atomic
    def import_services(self):
        return import_services(logger=self.logger, noop=False, importer=self)

    def handle(self, **options):
        self.options = options
        self.verbosity = int(options.get('verbosity', 1))
        self.org_syncher = None
        self.dept_syncher = None
        self.logger = logging.getLogger(__name__)
        self.services_changed = False
        self.count_services = set()
        self.keywords = {}
        for lang in self.supported_languages:
            kw_list = Keyword.objects.filter(language=lang)
            kw_dict = {kw.name: kw for kw in kw_list}
            self.keywords[lang] = kw_dict
        self.keywords_by_id = {kw.pk: kw for kw in Keyword.objects.all()}

        #if options['cached']:
        #    requests_cache.install_cache('services_import')

        # Activate the default language for the duration of the import
        # to make sure translated fields are populated correctly.
        old_lang = get_language()
        activate(settings.LANGUAGES[0][0])

        import_count = 0
        for imp in self.importer_types:
            if not self.options[imp]:
                continue
            method = getattr(self, "import_%s" % imp)
            if self.verbosity:
                print("Importing %s..." % imp)
            method()
            import_count += 1

        #if self.services_changed:
        #    self.update_root_services()
        #if self.count_services:
        #    self.update_unit_counts()
        #self.update_division_units()

        if not import_count:
            sys.stderr.write("Nothing to import.\n")
        activate(old_lang)




