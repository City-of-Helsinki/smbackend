import datetime
import hashlib
import json
import logging
import os
from collections import defaultdict
from operator import itemgetter

import pytz
from django import db
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import Point, Polygon
from munigeo.importer.sync import ModelSyncher
from munigeo.models import AdministrativeDivisionGeometry, Municipality

from services.management.commands.services_import.departments import import_departments
from services.management.commands.services_import.keyword import KeywordHandler
from services.models import (
    AccessibilityVariable,
    Department,
    MobilityServiceNode,
    Service,
    ServiceNode,
    Unit,
    UnitAccessibilityProperty,
    UnitAccessibilityShortcomings,
    UnitConnection,
    UnitIdentifier,
    UnitServiceDetails,
)
from services.models.unit import ORGANIZER_TYPES, PROJECTION_SRID, PROVIDER_TYPES
from services.utils import AccessibilityShortcomingCalculator

from .utils import (
    clean_latin1,
    clean_text,
    pk_get,
    postcodes,
    save_translated_field,
    update_extra_searchwords,
    update_service_names_fields,
)

UTC_TIMEZONE = pytz.timezone("UTC")
ACTIVE_TIMEZONE = pytz.timezone(settings.TIME_ZONE)
ACCESSIBILITY_VARIABLES = None
EXISTING_SERVICE_NODE_IDS = None
EXISTING_MOBILITY_SERVICE_NODE_IDS = None
EXISTING_SERVICE_IDS = None
LOGGER = None
VERBOSITY = False


def get_accessibility_variables():
    global ACCESSIBILITY_VARIABLES
    if ACCESSIBILITY_VARIABLES is None:
        ACCESSIBILITY_VARIABLES = {x.id: x for x in AccessibilityVariable.objects.all()}
    return ACCESSIBILITY_VARIABLES


def get_service_node_ids():
    global EXISTING_SERVICE_NODE_IDS
    if EXISTING_SERVICE_NODE_IDS is None:
        EXISTING_SERVICE_NODE_IDS = set(
            ServiceNode.objects.values_list("id", flat=True)
        )
    return EXISTING_SERVICE_NODE_IDS


def get_mobility_service_node_ids():
    global EXISTING_MOBILITY_SERVICE_NODE_IDS
    if EXISTING_MOBILITY_SERVICE_NODE_IDS is None:
        EXISTING_MOBILITY_SERVICE_NODE_IDS = set(
            MobilityServiceNode.objects.values_list("id", flat=True)
        )
    return EXISTING_MOBILITY_SERVICE_NODE_IDS


def get_service_ids():
    global EXISTING_SERVICE_IDS
    if EXISTING_SERVICE_IDS is None:
        EXISTING_SERVICE_IDS = set(Service.objects.values_list("id", flat=True))
    return EXISTING_SERVICE_IDS


def _fetch_units():
    if VERBOSITY:
        LOGGER.info("Fetching units")
    return pk_get("unit", params={"official": "yes", "newfeatures": "yes"})


def import_units(
    dept_syncher=None,
    fetch_only_id=None,
    verbosity=True,
    logger=None,
    fetch_units=_fetch_units,
    fetch_resource=pk_get,
):
    global VERBOSITY, LOGGER, EXISTING_SERVICE_NODE_IDS, EXISTING_SERVICE_IDS

    EXISTING_SERVICE_NODE_IDS = None
    EXISTING_SERVICE_IDS = None

    VERBOSITY = verbosity
    LOGGER = logger

    keyword_handler = KeywordHandler(verbosity=verbosity, logger=logger)

    if VERBOSITY and not LOGGER:
        LOGGER = logging.getLogger(__name__)

    muni_by_name = {muni.name_fi.lower(): muni for muni in Municipality.objects.all()}

    if not dept_syncher:
        dept_syncher = import_departments(noop=True)
    department_id_to_uuid = dict(
        ((k, str(v)) for k, v in Department.objects.all().values_list("id", "uuid"))
    )

    VERBOSITY and LOGGER.info("Fetching unit connections %s" % dept_syncher)

    connections = fetch_resource("connection")
    conn_by_unit = defaultdict(list)
    for conn in connections:
        unit_id = conn["unit_id"]
        conn_by_unit[unit_id].append(conn)

    VERBOSITY and LOGGER.info("Fetching accessibility properties")

    # acc_properties = self.fetch_resource('accessibility_property', v3=True)
    acc_properties = fetch_resource("accessibility_property")
    acc_by_unit = defaultdict(list)
    for ap in acc_properties:
        unit_id = ap["unit_id"]
        acc_by_unit[unit_id].append(ap)

    VERBOSITY and LOGGER.info("Fetching ontologyword details")

    details = fetch_resource("ontologyword_details")
    ontologyword_details_by_unit = defaultdict(list)
    for detail in details:
        unit_id = detail["unit_id"]
        ontologyword_details_by_unit[unit_id].append(detail)

    target_srid = PROJECTION_SRID
    bounding_box = Polygon.from_bbox(settings.BOUNDING_BOX)
    bounding_box.srid = 4326
    gps_srs = SpatialReference(4326)
    target_srs = SpatialReference(target_srid)
    target_to_gps_ct = CoordTransform(target_srs, gps_srs)
    bounding_box.transform(target_to_gps_ct)
    gps_to_target_ct = CoordTransform(gps_srs, target_srs)

    if fetch_only_id:
        obj_id = fetch_only_id
        obj_list = [
            fetch_resource(
                "unit", obj_id, params={"official": "yes", "newfeatures": "yes"}
            )
        ]
        queryset = Unit.objects.filter(id=obj_id)
    else:
        obj_list = fetch_units()
        queryset = Unit.objects.all().prefetch_related(
            "services", "keywords", "service_details"
        )

    syncher = ModelSyncher(queryset, lambda obj: obj.id)
    for info in obj_list:
        uid = info["id"]
        info["connections"] = conn_by_unit.get(uid, [])
        info["accessibility_properties"] = acc_by_unit.get(uid, [])
        info["service_details"] = ontologyword_details_by_unit.get(uid, [])
        _import_unit(
            syncher,
            keyword_handler,
            info.copy(),
            dept_syncher,
            muni_by_name,
            bounding_box,
            gps_to_target_ct,
            target_srid,
            department_id_to_uuid,
        )

    syncher.finish()
    return dept_syncher, syncher


def _load_postcodes():
    path = os.path.join(settings.BASE_DIR, "data", "fi", "postcodes.txt")
    postcodes = {}
    try:
        f = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        return
    for line in f.readlines():
        code, muni = line.split(",")
        postcodes[code] = muni.strip()
    return postcodes


def _get_department_root_from_syncher(syncher, department, department_id_to_uuid):
    if department is None:
        return None
    if department.level == 0:
        return department
    parent = syncher.get(department_id_to_uuid.get(department.parent_id))
    return _get_department_root_from_syncher(syncher, parent, department_id_to_uuid)


@db.transaction.atomic
def _import_unit(
    syncher,
    keyword_handler,
    info,
    dept_syncher,
    muni_by_name,
    bounding_box,
    gps_to_target_ct,
    target_srid,
    department_id_to_uuid,
):
    obj = syncher.get(info["id"])
    obj_changed = False
    obj_created = False
    if not obj:
        obj = Unit(id=info["id"])
        obj_changed = True
        obj_created = True

    fields_that_need_translation = (
        "name",
        "street_address",
        "www",
        "picture_caption",
        "address_postal_full",
        "call_charge_info",
        "displayed_service_owner",
    )
    for field in fields_that_need_translation:
        if save_translated_field(obj, field, info, field):
            obj_changed = True
    fields_that_need_translation_and_renaming = (
        ("desc", "description"),
        ("short_desc", "short_description"),
    )
    for s_field, d_field in fields_that_need_translation_and_renaming:
        if save_translated_field(obj, d_field, info, s_field):
            obj_changed = True

    if "address_city_fi" not in info and "latitude" in info and "longitude" in info:
        if VERBOSITY:
            LOGGER.warning("%s: coordinates present but no city" % obj)

    municipality_id = None

    muni_name = info.get("address_city_fi", None)
    if not muni_name and "address_zip" in info:
        muni_name = "no-city"
    if muni_name:
        muni_name = muni_name.lower()
        if muni_name not in muni_by_name:
            postcode = info.get("address_zip", None)
            muni_name = postcodes().get(postcode, None)
            if muni_name:
                if VERBOSITY:
                    LOGGER.warning(
                        "%s: municipality to %s based on post code %s (was %s)"
                        % (obj, muni_name, postcode, info.get("address_city_fi"))
                    )
                muni_name = muni_name.lower()
    if muni_name:
        muni = muni_by_name.get(muni_name)
        if muni:
            municipality_id = muni.id
        else:
            if VERBOSITY:
                LOGGER.warning(
                    "%s: municipality %s not found from current Municipalities"
                    % (obj, muni_name)
                )

    if municipality_id and municipality_id != obj.municipality_id:
        obj.municipality_id = municipality_id
        obj_changed = True

    dept = None
    dept_id = None
    if "dept_id" in info:
        dept_id = info["dept_id"]
        dept = dept_syncher.get(dept_id)

    if not dept:
        LOGGER.warning("Missing department {} for unit {}".format(dept_id, obj.id))
    elif obj.department_id != dept.id:
        obj.department = dept
        obj_changed = True

    root_department = _get_department_root_from_syncher(
        dept_syncher, obj.department, department_id_to_uuid
    )
    if (root_department is None and obj.root_department_id is not None) or (
        root_department is not None and root_department.id != obj.root_department_id
    ):
        obj.root_department = root_department
        obj_changed = True

    fields = [
        "address_zip",
        "phone",
        "email",
        "fax",
        "provider_type",
        "organizer_type",
        "picture_url",
        "picture_entrance_url",
        "accessibility_www",
        "accessibility_phone",
        "accessibility_email",
        "streetview_entrance_url",
        "organizer_name",
        "organizer_business_id",
        "displayed_service_owner_type",
        "vtj_prt",
        "vtj_prt_verified",
    ]

    if info.get("provider_type"):
        provider_types = [
            val for val, str_val in PROVIDER_TYPES if str_val == info["provider_type"]
        ]
        info["provider_type"] = (
            provider_types[0] if provider_types else 7
        )  # 7 is unknown value
    if info.get("organizer_type"):
        organizer_types = [
            val for val, str_val in ORGANIZER_TYPES if str_val == info["organizer_type"]
        ]
        info["organizer_type"] = (
            organizer_types[0] if organizer_types else 11
        )  # 11 is unknown value

    for field in fields:
        if field not in info or clean_text(info[field]) == "":
            if getattr(obj, field) is not None:
                setattr(obj, field, None)
                obj_changed = True
        elif info[field] != getattr(obj, field):
            setattr(obj, field, clean_text(info.get(field)))
            obj_changed = True

    for field in ["created_time"]:
        if info.get(field):
            value = ACTIVE_TIMEZONE.localize(
                datetime.datetime.strptime(info.get(field), "%Y-%m-%dT%H:%M:%S")
            )
            if getattr(obj, field) != value:
                obj_changed = True
                setattr(obj, field, value)

    viewpoints = _parse_accessibility_viewpoints(info["accessibility_viewpoints"])
    if obj.accessibility_viewpoints != viewpoints:
        obj_changed = True
        obj.accessibility_viewpoints = viewpoints

    data_source = clean_text(info.get("data_source_url", None))
    if data_source == "":
        data_source = None
    if obj.data_source != data_source:
        obj_changed = True
        obj.data_source = data_source

    n = info.get("latitude", 0)
    e = info.get("longitude", 0)
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

    if obj.municipality_id is None and obj.location is not None:
        div = AdministrativeDivisionGeometry.objects.select_related(
            "division", "division__type"
        ).filter(boundary__contains=obj.location, division__type__type="muni")
        if div:
            if len(div) > 1:
                LOGGER.warning(
                    "Multiple municipalities found for unit {}!".format(obj.id)
                )
            muni_name = div[0].division.name_fi.lower()
            muni = muni_by_name.get(muni_name)
            obj.municipality = muni
            if muni is not None:
                LOGGER.info(
                    "Municipality_id added according to unit {}'s location.".format(
                        obj.id
                    )
                )

    is_public = info.get("is_public", True)
    # assumption: is_public field is missing only when fetching only public units
    if is_public != obj.public:
        obj_changed = True
        obj.public = is_public

    # if unit was previously soft-deleted, make it active again
    if not obj.is_active:
        obj_changed = True
        obj.is_active = True
        obj.deleted_at = None

    maintenance_organization = muni_name
    if obj.extensions is None:
        obj.extensions = {}
    if obj.extensions.get("maintenance_organization") != maintenance_organization:
        obj_changed = True
        obj.extensions["maintenance_organization"] = maintenance_organization
    if obj.extensions.get("maintenance_group") is None:
        obj_changed = True
        obj.extensions["maintenance_group"] = "kaikki"

    if obj_changed:
        if obj_created:
            verb = "created"
        else:
            verb = "changed"
        if VERBOSITY:
            LOGGER.info("%s %s" % (obj, verb))
        obj.last_modified_time = datetime.datetime.now(UTC_TIMEZONE)
        obj_changed = False
        try:
            obj.save()
        except db.utils.DataError as e:
            LOGGER.error("Importing failed for unit {}".format(str(obj)))
            raise e

    update_fields = ["last_modified_time"]

    obj_changed, update_fields = _import_unit_service_nodes(
        obj, info, obj_changed, update_fields
    )
    obj_changed, update_fields = _import_unit_mobility_service_nodes(
        obj, info, obj_changed, update_fields
    )
    obj_changed, update_fields = _import_unit_services(
        obj, info, obj_changed, update_fields
    )
    obj_changed, update_fields = update_service_names_fields(
        obj, info, obj_changed, update_fields
    )
    obj_changed = keyword_handler.sync_searchwords(obj, info, obj_changed)
    obj_changed, update_fields = update_extra_searchwords(
        obj, info, obj_changed, update_fields
    )
    obj_changed, update_fields = _import_unit_accessibility_variables(
        obj, info, obj_changed, update_fields
    )
    obj_changed, update_fields = _import_unit_connections(
        obj, info, obj_changed, update_fields
    )
    obj_changed, update_fields = _import_unit_sources(
        obj, info, obj_changed, update_fields
    )

    if obj_changed:
        obj.last_modified_time = datetime.datetime.now(UTC_TIMEZONE)
        obj.save(update_fields=update_fields)

    syncher.mark(obj)


def _import_unit_service_nodes(obj, info, obj_changed, update_fields):
    service_node_ids = sorted(
        [
            sid
            for sid in info.get("ontologytree_ids", [])
            if sid in get_service_node_ids()
        ]
    )

    obj_service_node_ids = sorted(obj.service_nodes.values_list("id", flat=True))

    if obj_service_node_ids != service_node_ids:
        obj.service_nodes.set(service_node_ids)

        # Update root service cache
        obj.root_service_nodes = ",".join(str(x) for x in obj.get_root_service_nodes())
        update_fields.append("root_service_nodes")
        obj_changed = True

    return obj_changed, update_fields


def _import_unit_mobility_service_nodes(obj, info, obj_changed, update_fields):
    mobility_service_node_ids = sorted(
        [
            sid
            for sid in info.get("ontologytree_ids", [])
            if sid in get_mobility_service_node_ids()
        ]
    )

    obj_mobility_service_node_ids = sorted(
        obj.mobility_service_nodes.values_list("id", flat=True)
    )

    if obj_mobility_service_node_ids != mobility_service_node_ids:
        obj.mobility_service_nodes.set(mobility_service_node_ids)
        obj_changed = True

    return obj_changed, update_fields


def _clean_service_details(info_dict):
    schoolyear = info_dict.get("schoolyear")
    if schoolyear is not None and len(schoolyear) > 0:
        start, end = clean_latin1(schoolyear).split("-")
        info_dict["period_begin_year"] = start
        info_dict["period_end_year"] = end
    return info_dict


def _service_key(info):
    keys = ("unit_id", "ontologyword_id")
    if "schoolyear" in info:
        keys += ("schoolyear",)
    if "clarification_fi" in info:
        keys += ("clarification_fi",)
    return itemgetter(*keys)(info)


def _import_unit_services(obj, info, obj_changed, update_fields):
    if info["service_details"]:
        owd = sorted(info["service_details"], key=_service_key)
        owd_json = json.dumps(owd, ensure_ascii=False, sort_keys=True).encode("utf8")
        owd_hash = hashlib.sha1(owd_json).hexdigest()
    else:
        owd_hash = None

    if obj.service_details_hash != owd_hash:
        if VERBOSITY:
            LOGGER.info(
                "%s service details set changed (%s vs. %s)"
                % (obj, obj.service_details_hash, owd_hash)
            )
        obj.service_details.all().delete()
        for owd in info["service_details"]:
            d = _clean_service_details(owd)
            unit_owd = UnitServiceDetails(unit=obj, service_id=d["ontologyword_id"])
            if "period_begin_year" in d:
                unit_owd.period_begin_year = d["period_begin_year"]
                unit_owd.period_end_year = d["period_end_year"]

            save_translated_field(
                unit_owd, "clarification", d, "clarification", max_length=200
            )
            unit_owd.save()

        obj.service_details_hash = owd_hash

        obj_changed = True
        update_fields.append("service_details_hash")

    return obj_changed, update_fields


def _import_unit_accessibility_variables(obj, info, obj_changed, update_fields):
    if info["accessibility_properties"]:
        acp = sorted(info["accessibility_properties"], key=itemgetter("variable_id"))
        acp_json = json.dumps(acp, ensure_ascii=False, sort_keys=True).encode("utf8")
        acp_hash = hashlib.sha1(acp_json).hexdigest()
    else:
        acp_hash = None
    if obj.accessibility_property_hash != acp_hash:
        if VERBOSITY:
            LOGGER.info(
                "%s accessibility property set changed (%s vs. %s)"
                % (obj, obj.accessibility_property_hash, acp_hash)
            )
        obj.accessibility_properties.all().delete()
        for acp in info["accessibility_properties"]:
            uap = UnitAccessibilityProperty(unit=obj)
            var_id = acp["variable_id"]
            if var_id not in get_accessibility_variables():
                var = AccessibilityVariable(id=var_id, name=acp["variable_name"])
                var.save()
            else:
                var = get_accessibility_variables()[var_id]
            uap.variable = var
            uap.value = acp["value"]
            uap.save()

        obj.accessibility_property_hash = acp_hash
        obj_changed = True
        update_fields.append("accessibility_property_hash")

        # Recalculate accessibility shortcomings
        description, shortcoming_count = AccessibilityShortcomingCalculator().calculate(
            obj
        )
        UnitAccessibilityShortcomings.objects.update_or_create(
            unit=obj,
            defaults={
                "accessibility_shortcoming_count": shortcoming_count,
                "accessibility_description": description,
            },
        )

    return obj_changed, update_fields


def _import_unit_connections(obj, info, obj_changed, update_fields):
    if info["connections"]:
        conn_json = json.dumps(
            info["connections"], ensure_ascii=False, sort_keys=True
        ).encode("utf8")
        conn_hash = hashlib.sha1(conn_json).hexdigest()
    else:
        conn_hash = None

    if obj.connection_hash != conn_hash:
        if VERBOSITY:
            LOGGER.info(
                "%s connection set changed (%s vs. %s)"
                % (obj, obj.connection_hash, conn_hash)
            )
        obj.connections.all().delete()

        for i, conn in enumerate(info["connections"]):
            c = UnitConnection(unit=obj)
            save_translated_field(c, "name", conn, "name", max_length=2100)
            save_translated_field(c, "www", conn, "www")
            section_type = [
                val
                for val, str_val in UnitConnection.SECTION_TYPES
                if str_val == conn["section_type"]
            ][0]
            assert section_type
            c.section_type = section_type

            c.order = i

            tags = conn.get("tags", [])
            if tags and c.tags != tags:
                c.tags = tags
                c._changed = True

            fields = ["email", "phone", "contact_person"]
            for field in fields:
                val = conn.get(field, None)
                if val and len(val) > UnitConnection._meta.get_field(field).max_length:
                    LOGGER.info(
                        "Ignoring too long value of field {field} in unit {obj.pk}"
                        " connections"
                    )
                    continue
                if getattr(c, field) != val:
                    setattr(c, field, val)
                    c._changed = True
            c.save()
        obj.connection_hash = conn_hash
        obj_changed = True
        update_fields.append("connection_hash")
    return obj_changed, update_fields


def _import_unit_sources(obj, info, obj_changed, update_fields):
    if "sources" in info:
        id_json = json.dumps(
            info["sources"], ensure_ascii=False, sort_keys=True
        ).encode("utf8")
        id_hash = hashlib.sha1(id_json).hexdigest()
    else:
        id_hash = None
    if obj.identifier_hash != id_hash:
        if VERBOSITY:
            LOGGER.info(
                "%s identifier set changed (%s vs. %s)"
                % (obj, obj.identifier_hash, id_hash)
            )
        obj.identifiers.all().delete()
        if id_hash is not None:
            for uid in info["sources"]:
                ui = UnitIdentifier(unit=obj)
                ui.namespace = uid.get("source")
                ui.value = uid.get("id")
                ui.save()

        obj.identifier_hash = id_hash
        obj_changed = True
        update_fields.append("identifier_hash")

    return obj_changed, update_fields


def _parse_accessibility_viewpoints(acc_viewpoints_str, drop_unknowns=False):
    viewpoints = {}
    all_unknown = True

    for viewpoint in acc_viewpoints_str.split(","):
        viewpoint_id, viewpoint_value = viewpoint.split(":")
        if viewpoint_value == "unknown":
            if not drop_unknowns:
                viewpoints[viewpoint_id] = None
        else:
            viewpoints[viewpoint_id] = viewpoint_value

            if all_unknown:
                all_unknown = False

    if all_unknown:
        return None
    return viewpoints
