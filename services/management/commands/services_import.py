# -*- coding: utf-8 -*-

import sys
import re
import os
import json
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

URL_BASE = 'http://www.hel.fi/palvelukarttaws/rest/v3/'
GK25_SRID = 3879

UTC_TIMEZONE = pytz.timezone('UTC')

class Command(BaseCommand):
    help = "Import services from Palvelukartta REST API"
    option_list = list(BaseCommand.option_list + (
        make_option('--cached', dest='cached', action='store_true', help='cache HTTP requests'),
        make_option('--single', dest='single', action='store', metavar='ID', type='string', help='import only single entity'),
    ))

    importer_types = ['organizations', 'departments', 'services', 'units', 'aliases']
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
        remove_ids = []
        for child_id in srv['child_ids']:
            if child_id not in service_dict:
                self.logger.error("Child service %d for service %d not found" % (child_id, srv['id']))
                remove_ids.append(child_id)
                continue
            child = service_dict[child_id]
            self.mark_service_depths(service_dict, child, level + 1)
        for child_id in remove_ids:
            srv['child_ids'].remove(child_id)

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
            service_ids = unit.get('service_ids', [])
            # Make note of what units supply each service. If the unit sets
            # and names for services match, we treat them as identical.
            remove_ids = []
            for srv_id in sorted(service_ids):
                if srv_id not in service_dict:
                    self.logger.error("Service %d (in unit %d) not found" % (srv_id, unit['id']))
                    remove_ids.append(srv_id)
                    continue
                srv = service_dict[srv_id]
                srv['units'].append(unit['id'])

            for srv_id in remove_ids:
                service_ids.remove(srv_id)

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

        if self.verbosity:
            self.logger.info("Found %d duplicate services" % count)

    @db.transaction.atomic
    def import_services(self):
        srv_list = self.pk_get('service')
        syncher = ModelSyncher(Service.objects.all(), lambda obj: obj.id)

        self.detect_duplicate_services(srv_list)

        additional_root_services = [
            {
                'name_fi': 'Asuminen ja kaupunkiympäristö',
                'name_en': 'Housing and urban environment',
                'name_sv': 'Boende och stadsmiljö',
                'id': 50000
            }, {
                'name_fi': 'Työ, talous ja hallinto',
                'name_en': 'Employment, economy and administration',
                'name_sv': 'Arbete, ekonomi och förvaltning',
                'id': 50001
            }, {
                'name_fi': 'Kulttuuri, liikunta ja vapaa-aika',
                'name_en': 'Culture, sports and leisure',
                'name_sv': 'Kultur, motion och fritid',
                'id': 50002
            }, {
                'name_fi': 'Liikenne ja kartat',
                'name_en': 'Traffic and maps',
                'name_sv': 'Trafik och kartor',
                'id': 50003
            },
        ]

        service_to_new_root = {
            25298: 50000, 25142: 50000,
            26098: 50001, 26300: 50001, 26244: 50001,
            25622: 50002, 28128: 50002, 25954: 50002,
            25554: 50003, 25476: 50003
        }

        dupes = []

        def handle_service(d):
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

            new_root = service_to_new_root.get(d['id'])
            if new_root:
                d['parent_id'] = new_root

            if 'parent_id' in d:
                parent = syncher.get(d['parent_id'])
                assert parent
            else:
                parent = None
            if obj.parent != parent:
                obj.parent = parent
                obj._changed = True

            self._sync_searchwords(obj, d)

            if obj._changed:
                obj.unit_count = obj.get_unit_count()
                obj.last_modified_time = datetime.now(UTC_TIMEZONE)
                obj.save()
                self.services_changed = True
            syncher.mark(obj)

        for d in additional_root_services:
            handle_service(d)
        for d in srv_list:
            handle_service(d)

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

        if not 'address_city_fi' in info and 'latitude' in info and 'longitude' in info:
            if self.verbosity:
                self.logger.warning("%s: coordinates present but no city" % obj)
        municipality_id = None
        muni_name = info.get('address_city_fi', None)
        if not muni_name and 'address_zip' in info:
            muni_name = 'no-city'
        if muni_name:
            muni_name = muni_name.lower()
            if muni_name in ('helsingin kaupunki',):
                muni_name = 'helsinki'
            elif muni_name in ('vantaan kaupunki',):
                muni_name = 'vantaa'
            elif muni_name in ('espoon kaupunki',):
                muni_name = 'espoo'
            if muni_name not in self.muni_by_name:
                postcode = info.get('address_zip', None)
                muni_name = self.postcodes.get(postcode, None)
                if muni_name:
                    if self.verbosity:
                        self.logger.warning('%s: municipality to %s based on post code %s (was %s)' % (obj, muni_name, postcode, info.get('address_city_fi')))
                    muni_name = muni_name.lower()
            if muni_name:
                muni = self.muni_by_name[muni_name]
                municipality_id = muni.id

        self._set_field(obj, 'municipality_id', municipality_id)

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
        for field_name in fields:
            val = info.get(field_name, None)
            if getattr(obj, field_name) != val:
                setattr(obj, field_name, val)
                field = obj._meta.get_field(field_name)
                max_length = getattr(field, 'max_length', 0)
                if max_length and val and len(val) > max_length and self.verbosity:
                    self.logger.error("Field '%s' too long (data: %s)" % (field_name, val))
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
                if self.verbosity:
                    print("Invalid coordinates (%f, %f) for %s" % (n, e, obj))

        if location and obj.location:
            # If the distance is less than 10cm, assume the location
            # hasn't changed.
            assert obj.location.srid == PROJECTION_SRID
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
            if self.verbosity:
                print("%s %s" % (obj, verb))
            obj.origin_last_modified_time = datetime.now(UTC_TIMEZONE)
            obj._changed = False
            obj.save()

        update_fields = ['origin_last_modified_time']

        service_ids = sorted([
            sid for sid in info.get('service_ids', [])
            if sid in self.existing_service_ids])

        obj_service_ids = sorted(obj.services.values_list('id', flat=True))
        if obj_service_ids != service_ids:
            if not obj._created and self.verbosity:
                print("%s service set changed: %s -> %s" % (obj, obj_service_ids, service_ids))
            obj.services = service_ids

            for srv_id in service_ids:
                self.count_services.add(srv_id)

            # Update root service cache
            obj.root_services = ','.join(str(x) for x in obj.get_root_services())
            update_fields.append('root_services')
            obj._changed = True

        self._sync_searchwords(obj, info)

        if info['connections']:
            conn_json = json.dumps(info['connections'], ensure_ascii=False, sort_keys=True).encode('utf8')
            conn_hash = hashlib.sha1(conn_json).hexdigest()
        else:
            conn_hash = None
        if obj.connection_hash != conn_hash:
            if self.verbosity:
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
            obj._changed = True
            update_fields.append('connection_hash')

        if info['accessibility_properties']:
            acp_json = json.dumps(info['accessibility_properties'], ensure_ascii=False, sort_keys=True).encode('utf8')
            acp_hash = hashlib.sha1(acp_json).hexdigest()
        else:
            acp_hash = None
        if obj.accessibility_property_hash != acp_hash:
            if self.verbosity:
                self.logger.info("%s accessibility property set changed (%s vs. %s)" %
                                 (obj, obj.accessibility_property_hash, acp_hash))
            obj.accessibility_properties.all().delete()
            for acp in info['accessibility_properties']:
                uap = UnitAccessibilityProperty(unit=obj)
                var_id = acp['variable_id']
                if var_id not in self.accessibility_variables:
                    var = AccessibilityVariable(id=var_id, name=acp['variable_name'])
                    var.save()
                else:
                    var = self.accessibility_variables[var_id]
                uap.variable = var
                uap.value = acp['value']
                uap.save()

            obj.accessibility_property_hash = acp_hash
            obj._changed = True
            update_fields.append('accessibility_property_hash')

        if info['sources']:
            id_json = json.dumps(info['sources'], ensure_ascii=False, sort_keys=True).encode('utf8')
            id_hash = hashlib.sha1(id_json).hexdigest()
        else:
            id_hash = None
        if obj.identifier_hash != id_hash:
            if self.verbosity:
                self.logger.info("%s identifier set changed (%s vs. %s)" %
                                 (obj, obj.identifier_hash, id_hash))
            obj.identifiers.all().delete()
            for uid in info['sources']:
                ui = UnitIdentifier(unit=obj)
                ui.namespace = uid.get('source')
                ui.value = uid.get('id')
                ui.save()

            obj.identifier_hash = id_hash
            obj._changed = True
            update_fields.append('identifier_hash')


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
            obj.save(update_fields=update_fields)

        syncher.mark(obj)

    def _fetch_units(self):
        if hasattr(self, 'unit_list'):
            return self.unit_list
        if self.verbosity:
            self.logger.info("Fetching units")
        obj_list = self.pk_get('unit')
        self.unit_list = obj_list
        return obj_list

    def _load_postcodes(self):
        path = os.path.join(settings.BASE_DIR, 'data', 'fi', 'postcodes.txt')
        self.postcodes = {}
        try:
            f = open(path, 'r')
        except FileNotFoundError:
            return
        for l in f.readlines():
            code, muni = l.split(',')
            self.postcodes[code] = muni.strip()

    def import_units(self):
        self._load_postcodes()
        self.muni_by_name = {muni.name_fi.lower(): muni for muni in Municipality.objects.all()}
        if self.existing_service_ids == None or len(self.existing_service_ids) < 1:
            self.existing_service_ids = set(Service.objects.values_list('id', flat=True))

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
            queryset = Unit.objects.all().prefetch_related('services', 'keywords')

        if self.verbosity:
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

        self.accessibility_variables = {x.id: x for x in AccessibilityVariable.objects.all()}
        if self.verbosity:
            self.logger.info("Fetching accessibility properties")
        if self.options['single']:
            acc_properties = [self.pk_get('accessibility_property', obj_id)]
        else:
            acc_properties = self.pk_get('accessibility_property')
        acc_by_unit = {}
        for ap in acc_properties:
            unit_id = ap['unit_id']
            if unit_id not in acc_by_unit:
                acc_by_unit[unit_id] = []
            acc_by_unit[unit_id].append(ap)

        self.target_srid = PROJECTION_SRID
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
            acp_list = acc_by_unit.get(info['id'], [])
            info['accessibility_properties'] = acp_list
            self._import_unit(syncher, info)
        syncher.finish()

    def import_aliases(self):
        path = os.path.join(settings.BASE_DIR, 'data', 'school_ids.csv')
        try:
            f = open(path, 'r')
        except FileNotFoundError:
            print("Aliases file {} not found".format(path))
            return
        RELEVANT_COLS = [3, 5] # IMPORTANT: verify the ids are in these columns
        value_sets = {}
        reader = csv.reader(f, delimiter=',')
        next(reader)
        for row in reader:
            primary_id = row[1]
            value_sets[primary_id] = set(
                row[col] for col in RELEVANT_COLS
                if row[col] and row[col].strip != ""
            )
        if len(value_sets) == 0:
            print("No aliases found in file.")
            return
        counts = {'success': 0, 'duplicate': 0, 'notfound': 0}
        for primary, aliases in value_sets.items():
            try:
                unit = Unit.objects.get(pk=primary)
                for alias in aliases:
                    alias_object = UnitAlias(first=unit, second=alias)
                    try:
                        alias_object.save()
                        counts['success'] += 1
                    except db.IntegrityError:
                        counts['duplicate'] += 1
                        pass
            except Unit.DoesNotExist:
                counts['notfound'] += 1
        if counts['success']:
            print("Imported {} aliases.".format(counts['success']))
        if counts['notfound']:
            print("{} units not found.".format(counts['notfound']))
        if counts['duplicate']:
            print("Skipped {} aliases already in database.".format(counts['duplicate']))

    @db.transaction.atomic
    def update_root_services(self):
        if self.verbosity:
            print("Updating unit root services...")
        for unit in Unit.objects.all().only('id', 'root_services'):
            new_srv_list = ','.join([str(x) for x in unit.get_root_services()])
            if new_srv_list != unit.root_services:
                unit.root_services = new_srv_list
                unit.save(update_fields=['root_services'])

    @db.transaction.atomic
    def update_unit_counts(self):
        srv_set = self.count_services
        current_set = srv_set
        for i in range(0, 20): # Make sure we don't loop endlessly (shouldn't have 20 deep tree anyway)
            parent_ids = Service.objects.filter(id__in=current_set).values_list('parent', flat=True)
            if not parent_ids:
                break
            srv_set |= set(parent_ids)
            current_set = parent_ids
        if self.verbosity:
            print("Updating unit counts for %d services..." % len(srv_set))
        srv_list = Service.objects.filter(id__in=srv_set)
        for srv in srv_list:
            srv.unit_count = srv.get_unit_count()
            srv.save(update_fields=['unit_count'])

    @db.transaction.atomic
    def update_division_units(self):
        rescue_stations = Unit.objects.filter(services__id=26194)
        rescue_areas = AdministrativeDivision.objects.filter(type__type='rescue_area')
        # TODO: request this data to be added to pel_suojelupiiri
        mapping = {
            1: 8953,
            2: 8954,
            3: 8952,
            4: 8955,
            5: 8956,
            6: 8958,
            7: 8957,
            8: 8957
        }
        for area in rescue_areas:
            area.service_point_id = mapping[int(area.origin_id)]
            area.save()

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
            if self.verbosity:
                print("Importing %s..." % imp)
            method()
            import_count += 1

        if self.services_changed:
            self.update_root_services()
        if self.count_services:
            self.update_unit_counts()
        self.update_division_units()

        if not import_count:
            sys.stderr.write("Nothing to import.\n")
        activate(old_lang)
