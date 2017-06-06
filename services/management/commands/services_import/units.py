import datetime
import hashlib
import json
import pprint
import os
import logging

import pytz
from collections import defaultdict
from operator import itemgetter

from django import db
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from munigeo.importer.sync import ModelSyncher
from munigeo.models import Municipality

from services.management.commands.services_import.departments import import_departments
from services.management.commands.services_import.organizations import import_organizations
from services.models import Unit, OntologyTreeNode, OntologyWord, AccessibilityVariable, \
    Keyword, UnitConnection, UnitAccessibilityProperty, UnitIdentifier
from services.models.unit import PROJECTION_SRID, PROVIDER_TYPES
from services.models.unit_connection import SECTION_TYPES
from .utils import pk_get, save_translated_field, postcodes, keywords_by_id, keywords, SUPPORTED_LANGUAGES

UTC_TIMEZONE = pytz.timezone('UTC')
ACTIVE_TIMEZONE = pytz.timezone(settings.TIME_ZONE)
KEYWORDS = None
KEYWORDS_BY_ID = None
ACCESSIBILITY_VARIABLES = {x.id: x for x in AccessibilityVariable.objects.all()}
EXISTING_SERVICE_IDS = set(OntologyWord.objects.values_list('id', flat=True))
EXISTING_SERVICE_TREE_NODE_IDS = set(OntologyTreeNode.objects.values_list('id', flat=True))
LOGGER = None
VERBOSITY = False


def import_units(org_syncher=None, dept_syncher=None, fetch_only_id=None, verbosity=True, logger=None):
    global VERBOSITY, LOGGER, KEYWORDS_BY_ID, KEYWORDS
    VERBOSITY = verbosity
    LOGGER = logger

    if VERBOSITY and not LOGGER:
        LOGGER = logging.getLogger(__name__)

    KEYWORDS = keywords()
    KEYWORDS_BY_ID = keywords_by_id(KEYWORDS)

    _load_postcodes()
    muni_by_name = {muni.name_fi.lower(): muni for muni in Municipality.objects.all()}

    if not org_syncher:
        org_syncher = import_organizations(noop=True)

    if not dept_syncher:
        dept_syncher = import_departments(noop=True)

    VERBOSITY and LOGGER.info("Fetching unit connections %s %s" % (org_syncher, dept_syncher))

    connections = pk_get('connection')
    conn_by_unit = defaultdict(list)
    for conn in connections:
        unit_id = conn['unit_id']
        conn_by_unit[unit_id].append(conn)

    VERBOSITY and LOGGER.info("Fetching accessibility properties")

    # acc_properties = self.pk_get('accessibility_property', v3=True)
    acc_properties = pk_get('accessibility_property')
    acc_by_unit = defaultdict(list)
    for ap in acc_properties:
        unit_id = ap['unit_id']
        acc_by_unit[unit_id].append(ap)

    target_srid = PROJECTION_SRID
    bounding_box = Polygon.from_bbox(settings.BOUNDING_BOX)
    bounding_box.set_srid(4326)
    gps_srs = SpatialReference(4326)
    target_srs = SpatialReference(target_srid)
    target_to_gps_ct = CoordTransform(target_srs, gps_srs)
    bounding_box.transform(target_to_gps_ct)
    gps_to_target_ct = CoordTransform(gps_srs, target_srs)

    if fetch_only_id:
        obj_id = fetch_only_id
        obj_list = [pk_get('unit', obj_id, params={'official': 'yes'})]
        queryset = Unit.objects.filter(id=obj_id)
    else:
        obj_list = _fetch_units()
        queryset = Unit.objects.filter(data_source='tprek').prefetch_related('services', 'keywords')

    count_services = set()

    syncher = ModelSyncher(queryset, lambda obj: obj.id)
    for idx, info in enumerate(obj_list):
        conn_list = conn_by_unit.get(info['id'], [])
        info['connections'] = conn_list
        acp_list = acc_by_unit.get(info['id'], [])
        info['accessibility_properties'] = acp_list
        obj = _import_unit(syncher, info, org_syncher, dept_syncher, muni_by_name,
                           bounding_box, gps_to_target_ct, target_srid)
        #print(info['accessibility_viewpoints'])
        #print(_parse_accessibility_viewpoints(info['accessibility_viewpoints']))
        # _import_unit_services(obj, info, count_services)
    syncher.finish()

    return org_syncher, dept_syncher, syncher


def _load_postcodes():
    path = os.path.join(settings.BASE_DIR, 'data', 'fi', 'postcodes.txt')
    postcodes = {}
    try:
        f = open(path, 'r', encoding='utf-8')
    except FileNotFoundError:
        return
    for l in f.readlines():
        code, muni = l.split(',')
        postcodes[code] = muni.strip()
    return postcodes


def _fetch_units():
    if VERBOSITY:
        LOGGER.info("Fetching units")
    return pk_get('unit', params={'official': 'yes'})


@db.transaction.atomic
def _import_unit(syncher, info, org_syncher, dept_syncher, muni_by_name, bounding_box, gps_to_target_ct, target_srid):
    VERBOSITY and LOGGER.info(pprint.pformat(info))

    obj = syncher.get(info['id'])
    obj_changed = False
    obj_created = False
    if not obj:
        obj = Unit(id=info['id'])
        obj_changed = True
        obj_created = True

    # print('handling unit {} ({})'.format(info['name_fi'], info['id']))

    fields_that_need_translation = ('name', 'street_address', 'www', 'picture_caption', 'desc', 'short_desc',
                                    'address_city', 'address_postal_full', 'call_charge_info', 'extra_searchwords')
    for field in fields_that_need_translation:
        if save_translated_field(obj, field, info, field):
            obj_changed = True

    org_id = info['org_id']
    org = org_syncher.get(info['org_id'])
    # else:
    #     org = Organization.objects.get(id=org_id)
    # print('org id', org_id)

    assert org is not None

    if obj.organization_id != org_id:
        obj.organization = org
        obj_changed = True

    if not 'address_city_fi' in info and 'latitude' in info and 'longitude' in info:
        if VERBOSITY:
            LOGGER.warning("%s: coordinates present but no city" % obj)

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
        if muni_name not in muni_by_name:
            postcode = info.get('address_zip', None)
            muni_name = postcodes().get(postcode, None)
            if muni_name:
                if VERBOSITY:
                    LOGGER.warning('%s: municipality to %s based on post code %s (was %s)' %
                                   (obj, muni_name, postcode, info.get('address_city_fi')))
                muni_name = muni_name.lower()
        if muni_name:
            muni = muni_by_name.get(muni_name)
            if muni:
                municipality_id = muni.id
            else:
                if VERBOSITY:
                    LOGGER.warning('%s: municipality %s not found from current Municipalities' % (obj, muni_name))

    if municipality_id:
        # self._set_field(obj, 'municipality_id', municipality_id)
        obj.municipality_id = municipality_id

    dept = None
    dept_id = None
    if 'dept_id' in info:
        dept_id = info['dept_id']
        # if self.dept_syncher:
        dept = dept_syncher.get(dept_id)
        org = None
        if not dept:
            org = org_syncher.get(dept_id)
        # else:
        #     try:
        #         dept = Department.objects.get(id=dept_id)
        #     except Department.DoesNotExist:
        #         print("Department %s does not exist" % dept_id)
        #         raise

    if not dept:
        LOGGER.warning("Missing department {} for unit {}".format(dept_id, obj.id))
    elif obj.department_id != dept_id:
        obj.department = dept
        obj_changed = True

    fields = ['address_zip', 'phone', 'email', 'fax', 'provider_type', 'picture_url', 'picture_entrance_url',
              'accessibility_www', 'accessibility_phone', 'accessibility_email', 'streetview_entrance_url'
              ]

    if info.get('provider_type'):
        info['provider_type'] = [val for val, str_val in PROVIDER_TYPES if str_val == info['provider_type']][0]

    for field in fields:
        if info.get(field):
            if info[field] != getattr(obj, field):
                obj_changed = True
                setattr(obj, field, info.get(field))

    for field in ['created_time', 'modified_time']:
        if info.get(field):
            value = ACTIVE_TIMEZONE.localize(datetime.strptime(info.get(field), '%Y-%m-%dT%H:%M:%S'))
            if getattr(obj, field) != value:
                obj_changed = True
                setattr(obj, field, value)

    # url = info.get('data_source_url', None)
    # if url:
    #     if not url.startswith('http'):
    #         url = 'http://%s' % url
    # if obj.data_source_url != url:
    #     obj._changed = True
    #     obj.data_source_url = url

    viewpoints = _parse_accessibility_viewpoints(info['accessibility_viewpoints'])
    if obj.accessibility_viewpoints != viewpoints:
        obj_changed = True
        obj.accessibility_viewpoints = viewpoints

    data_source = 'tprek'
    if obj.data_source != data_source:
        obj_changed = True
        obj.data_source = data_source

    n = info.get('latitude', 0)
    e = info.get('longitude', 0)
    location = None
    if n and e:
        p = Point(e, n, srid=4326)  # GPS coordinate system
        if p.within(bounding_box):
            if target_srid != 4326:
                p.transform(gps_to_target_ct)
            location = p
        else:
            if VERBOSITY:
                LOGGER.warning("Invalid coordinates (%f, %f) for %s" % (n, e, obj))

    if location and obj.location:
        # If the distance is less than 10cm, assume the location
        # hasn't changed.
        assert obj.location.srid == PROJECTION_SRID
        if location.distance(obj.location) < 0.10:
            location = obj.location
    if location != obj.location:
        obj_changed = True
        obj.location = location
        # Assumption: this importer receives only
        # point geometries and any other geometries
        # are imported after the unit and point has been
        # imported.
        obj.geometry = location

    if obj.geometry is None and obj.location is not None:
        obj_changed = True
        obj.geometry = obj.location

    is_public = info.get('is_public', True)
    # assumption: is_public field is missing only when fetching only public units
    if is_public != obj.public:
        obj_changed = True
        obj.public = is_public

    if obj_changed:
        if obj_created:
            verb = "created"
        else:
            verb = "changed"
        if VERBOSITY:
            LOGGER.info("%s %s" % (obj, verb))
        obj.origin_last_modified_time = datetime.now(UTC_TIMEZONE)
        obj_changed = False
        obj.save()

    update_fields = ['modified_time']

    obj_changed, update_fields = _import_unit_services(obj, info, set(), obj_changed, update_fields)
    obj_changed = _sync_searchwords(obj, info, obj_changed)

    obj_changed, update_fields = _import_unit_accessibility_variables(obj, info, obj_changed, update_fields)
    obj_changed, update_fields = _import_unit_connections(obj, info, obj_changed, update_fields)
    obj_changed, update_fields = _import_unit_sources(obj, info, obj_changed, update_fields)

    if obj_changed:
        obj.origin_last_modified_time = datetime.now(UTC_TIMEZONE)
        obj.save(update_fields=update_fields)

    syncher.mark(obj)
    return obj


def _import_unit_services(obj, info, count_services, obj_changed, update_fields):
    ontologytreenode_ids = sorted([
        sid for sid in info.get('ontologytree_ids', [])
        if sid in EXISTING_SERVICE_TREE_NODE_IDS])
    # print("ontologytree_ids: %s -> %s" % (info.get('ontologytree_ids', []), servicenode_ids))

    obj_ontologytreenode_ids = sorted(obj.service_tree_nodes.values_list('id', flat=True))
    if obj_ontologytreenode_ids != ontologytreenode_ids:
        # if not obj_created and VERBOSITY:
        #     LOGGER.warning("%s service set changed: %s -> %s" % (obj, obj_servicenode_ids, servicenode_ids))
        obj.service_tree_nodes = ontologytreenode_ids

        for treenode_id in ontologytreenode_ids:
            count_services.add(treenode_id)

        # Update root service cache
        obj.root_ontologytreenodes = ','.join(str(x) for x in obj.get_root_ontologytreenodes())
        update_fields.append('root_ontologytreenodes')
        obj_changed=True

    return obj_changed, update_fields


def _sync_searchwords(obj, info, obj_changed):
    obj.new_keywords = set()
    for lang in SUPPORTED_LANGUAGES:
        _save_searchwords(obj, info, lang)

    old_kw_set = set(obj.keywords.all().values_list('pk', flat=True))
    if old_kw_set == obj.new_keywords:
        return obj_changed

    if VERBOSITY:
        old_kw_str = ', '.join([KEYWORDS_BY_ID[x].name for x in old_kw_set])
        new_kw_str = ', '.join([KEYWORDS_BY_ID[x].name for x in obj.new_keywords])
        LOGGER.info("%s keyword set changed: %s -> %s" % (obj, old_kw_str, new_kw_str))
    obj.keywords = list(obj.new_keywords)
    return True


def _save_searchwords(obj, info, language):
    field_name = 'extra_searchwords_%s' % language
    new_kw_set = set()
    if field_name in info:
        kws = [x.strip() for x in info[field_name].split(',')]
        kws = [x for x in kws if x]
        new_kw_set = set()
        for kw in kws:
            if not kw in KEYWORDS[language]:
                kw_obj = Keyword(name=kw, language=language)
                kw_obj.save()
                KEYWORDS[language][kw] = kw_obj
                KEYWORDS_BY_ID[kw_obj.pk] = kw_obj
            else:
                kw_obj = KEYWORDS[language][kw]
            new_kw_set.add(kw_obj.pk)
    return new_kw_set


def _import_unit_accessibility_variables(obj, info, obj_changed, update_fields):
    if info['accessibility_properties']:
        acp = sorted(info['accessibility_properties'], key=itemgetter('variable_id'))
        acp_json = json.dumps(acp, ensure_ascii=False, sort_keys=True).encode('utf8')
        acp_hash = hashlib.sha1(acp_json).hexdigest()
    else:
        acp_hash = None
    if obj.accessibility_property_hash != acp_hash:
        if VERBOSITY:
            LOGGER.info("%s accessibility property set changed (%s vs. %s)" %
                        (obj, obj.accessibility_property_hash, acp_hash))
        obj.accessibility_properties.all().delete()
        for acp in info['accessibility_properties']:
            uap = UnitAccessibilityProperty(unit=obj)
            var_id = acp['variable_id']
            if var_id not in ACCESSIBILITY_VARIABLES:
                var = AccessibilityVariable(id=var_id, name=acp['variable_name'])
                var.save()
            else:
                var = ACCESSIBILITY_VARIABLES[var_id]
            uap.variable = var
            uap.value = acp['value']
            uap.save()

        obj.accessibility_property_hash = acp_hash
        obj_changed = True
        update_fields.append('accessibility_property_hash')
    return obj_changed, update_fields


def _import_unit_connections(obj, info, obj_changed, update_fields):
    if info['connections']:
        conn_json = json.dumps(info['connections'], ensure_ascii=False, sort_keys=True).encode('utf8')
        conn_hash = hashlib.sha1(conn_json).hexdigest()
    else:
        conn_hash = None

    if obj.connection_hash != conn_hash:
        if VERBOSITY:
            LOGGER.info("%s connection set changed (%s vs. %s)" % (obj, obj.connection_hash, conn_hash))
        obj.connections.all().delete()

        for i, conn in enumerate(info['connections']):
            c = UnitConnection(unit=obj)
            save_translated_field(c, 'name', conn, 'name', max_length=400)
            save_translated_field(c, 'www', conn, 'www')
            section_type = [val for val, str_val in SECTION_TYPES if str_val == conn['section_type']][0]
            assert section_type
            c.section_type = section_type

            # print("------------- connection ----------------")
            # pprint.pprint(conn)
            # print("^^^^^^^^^^^^^ connection ^^^^^^^^^^^^^^^^")
            # c.section = conn['section_type'].lower()
            # {'contact_person': 'Miia Kovalainen',
            # 'email': 'miia.kovalainen@hel.fi',
            # 'name_en': 'Head of day care centre',
            # 'name_fi': 'Päiväkodinjohtaja',
            # 'name_sv': 'Daghemsföreståndare',
            # 'phone': '09 310 41571',
            # 'section_type': 'PHONE_OR_EMAIL',
            # 'unit_id': 1},

            # {'name_en': 'Application for day care',
            # 'name_fi': 'Täytä päivähoitohakemus',
            # 'name_sv': 'Ansökan om barndagvård',
            # 'section_type': 'LINK',
            # 'unit_id': 1,
            # 'www_en': 'http://www.hel.fi/www/helsinki/en/day-care-education/day-care/options/applying',
            # 'www_fi': 'http://www.hel.fi/www/Helsinki/fi/paivahoito-ja-koulutus/paivahoito/paivakotihoito/hakeminen',
            # 'www_sv': 'http://www.hel.fi/www/helsinki/sv/dagvard-och-utbildning/dagvord/ansokan/ansokan-dagvard'}

            c.order = i
            fields = ['email', 'phone', 'contact_person']
            for field in fields:
                val = conn.get(field, None)
                if val and len(val) > UnitConnection._meta.get_field(field).max_length:
                    LOGGER.info(
                        "Ignoring too long value of field {} in unit {} connections".format(
                            field, obj.pk))
                    continue
                if getattr(c, field) != val:
                    setattr(c, field, val)
                    c._changed = True
            c.save()
        obj.connection_hash = conn_hash
        obj_changed = True
        update_fields.append('connection_hash')
    return obj_changed, update_fields


def _import_unit_sources(obj, info, obj_changed, update_fields):
    if info['sources']:
        id_json = json.dumps(info['sources'], ensure_ascii=False, sort_keys=True).encode('utf8')
        id_hash = hashlib.sha1(id_json).hexdigest()
    else:
        id_hash = None
    if obj.identifier_hash != id_hash:
        if VERBOSITY:
            LOGGER.info("%s identifier set changed (%s vs. %s)" %
                        (obj, obj.identifier_hash, id_hash))
        obj.identifiers.all().delete()
        for uid in info['sources']:
            ui = UnitIdentifier(unit=obj)
            ui.namespace = uid.get('source')
            ui.value = uid.get('id')
            ui.save()

        obj.identifier_hash = id_hash
        obj_changed = True
        update_fields.append('identifier_hash')

    return obj_changed, update_fields


def _parse_accessibility_viewpoints(acc_viewpoints_str, drop_unknowns=True):
    viewpoints = {}
    all_unknown = True

    for viewpoint in acc_viewpoints_str.split(','):
        viewpoint_id, viewpoint_value = viewpoint.split(':')
        if viewpoint_value == "unknown":
            if not drop_unknowns:
                viewpoints[int(viewpoint_id)] = None
        else:
            viewpoints[int(viewpoint_id)] = viewpoint_value

            if all_unknown:
                all_unknown = False

    if drop_unknowns and all_unknown:
        return {}

    return viewpoints

