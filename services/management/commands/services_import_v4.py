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
from services.models import *

URL_BASE = 'http://www.hel.fi/palvelukarttaws/rest/v4/'
GK25_SRID = 3879

UTC_TIMEZONE = pytz.timezone('UTC')


class Command(BaseCommand):
    help = "Import services from Palvelukartta REST API"
    option_list = list(BaseCommand.option_list)
    #option_list = list(BaseCommand.option_list + (
    #    make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
    #    make_option('--single', dest='single', action='store', metavar='ID', type='string', help='import only single entity'),
    #))

    importer_types = ['services']
    supported_languages = ['fi', 'sv', 'en']

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            method = "import_%s" % imp
            assert getattr(self, method, False), "No importer defined for %s" % method
            opt = make_option('--%s' % imp, dest=imp, action='store_true', help='import %s' % imp)
            self.option_list.append(opt)
        self.services = {}
        self.existing_service_ids = None


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

    @db.transaction.atomic
    def import_services(self):
        ontologytrees = self.pk_get('ontologytree')
        ontologywords = self.pk_get('ontologyword')
        tree = self._build_servicetree(ontologytrees, ontologywords)
        #print('top lever ' + str(len(tree)))
        #print(str(tree[0]))
        nodesyncher = ModelSyncher(ServiceNode.objects.all(), lambda obj: obj.id)
        leafsyncher = ModelSyncher(ServiceLeaf.objects.all(), lambda obj: obj.id)


        def handle_servicenode(d):
            obj = nodesyncher.get(d['id'])
            if not obj:
                obj = ServiceNode(id=d['id'])
                obj._changed = True
            self._save_translated_field(obj, 'name', d, 'name')

            if 'parent_id' in d:
                parent = nodesyncher.get(d['parent_id'])
                assert parent
            else:
                parent = None
            if obj.parent != parent:
                obj.parent = parent
                obj._changed = True

            #self._sync_searchwords(obj, d)

            if obj._changed:
                #obj.unit_count = obj.get_unit_count()
                obj.last_modified_time = datetime.now(UTC_TIMEZONE)
                obj.save()
                self.services_changed = True
            nodesyncher.mark(obj)

            for child_node in d['children']:
                handle_servicenode(child_node)

            leaf_objs = []
            for leaf_node in d.get('leaves', []):
                leaf_obj = handle_serviceleaf(leaf_node)
                leaf_objs.append(leaf_obj)
            if set(obj.leaves.all().values_list('id', flat=True)) != set([l.id for l in leaf_objs]):
                obj.leaves.clear()
                for l in leaf_objs:
                    obj.leaves.add(l)


        def handle_serviceleaf(d):
            obj = leafsyncher.get(d['id'])
            if not obj:
                obj = ServiceLeaf(id=d['id'])
                obj._changed = True

            self._save_translated_field(obj, 'name', d, 'ontologyword')

            if obj._changed:
                #obj.unit_count = obj.get_unit_count()
                obj.last_modified_time = datetime.now(UTC_TIMEZONE)
                obj.save()
                self.services_changed = True

            return obj


        for d in tree:
            handle_servicenode(d)

        nodesyncher.finish()

    def _build_servicetree(self, ontologytrees, ontologywords):
        ontologywords_dict = {ow['id']: ow for ow in ontologywords}
        tree = [ot for ot in ontologytrees if not ot.get('parent_id')]
        for parent_ot in tree:
            self._add_ot_children(parent_ot, ontologytrees, ontologywords_dict)

            if parent_ot.get('ontologyword_reference'):
                parent_ot['leaves'] = []
                for ow_id in parent_ot.get('ontologyword_reference').replace('*', '+').split('+'):
                    parent_ot['leaves'].append(ontologywords_dict.get(int(ow_id)))

        return tree

    def _add_ot_children(self, parent_ot, ontologytrees, ontologywords_dict):
        parent_ot['children'] = [ot for ot in ontologytrees if
                                 ot.get('parent_id') == parent_ot['id']]

        for child_ot in parent_ot['children']:
            self._add_ot_children(child_ot, ontologytrees, ontologywords_dict)

        if parent_ot.get('ontologyword_reference'):
            parent_ot['leaves'] = []
            for ow_id in parent_ot.get('ontologyword_reference').replace('*', '+').split('+'):
                parent_ot['leaves'].append(ontologywords_dict.get(int(ow_id)))


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



