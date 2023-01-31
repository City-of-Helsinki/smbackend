import datetime
import hashlib
import os
import re
from functools import lru_cache

import pytz
import requests
import yaml
from django import db
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

from mobility_data.importers.utils import (
    create_mobile_unit_as_unit_reference,
    delete_mobile_units,
)
from services.management.commands.services_import.services import (
    update_service_counts,
    update_service_node_counts,
)
from services.models import Service, ServiceNode, Unit, UnitServiceDetails

# TODO: Change to production endpoint when available
TURKU_BASE_URL = "https://digiaurajoki.turku.fi:9443/kuntapalvelut/api/v1/"
ACCESSIBILITY_BASE_URL = "https://asiointi.hel.fi/kapaesteettomyys/api/v1/"
UTC_TIMEZONE = pytz.timezone("UTC")

data_path = os.path.join(os.path.dirname(__file__), "data")
EXTERNAL_SOURCES_CONFIG_FILE = f"{data_path}/external_units_config.yml"


def get_external_sources_yaml_config():
    config = yaml.safe_load(open(EXTERNAL_SOURCES_CONFIG_FILE, "r", encoding="utf-8"))
    return config["external_data_sources"]


def get_external_source_config(external_source_name):
    config = get_external_sources_yaml_config()
    for c in config:
        if c["name"] == external_source_name:
            return c
    return None


def get_configured_external_sources_names(config=None):
    if not config:
        config = get_external_sources_yaml_config()
    return [f["name"] for f in config]


def clean_text(text, default=None):
    if not isinstance(text, str):
        return text
    # remove consecutive whitespaces
    text = re.sub(r"\s\s+", " ", text, re.U)
    # remove nil bytes
    text = text.replace("\u0000", " ")
    text = text.replace("\r", "\n")
    text = text.replace("\\r", "\n")
    text = text.strip()
    if len(text) == 0:
        return default
    return text


def get_resource(url, headers=None):
    print("CALLING URL >>> ", url)
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, "status code {}".format(resp.status_code)
    return resp.json()


def get_turku_api_headers(content=""):
    application = "Palvelukartta"
    key = getattr(settings, "TURKU_API_KEY", "")
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    data = (application + timestamp + content + key).encode("utf-8")
    auth = hashlib.sha256(data)
    return {
        "Authorization": auth.hexdigest(),
        "X-TURKU-SP": application,
        "X-TURKU-TS": timestamp,
    }


def get_ar_resource(resource_name):
    url = "{}{}".format(ACCESSIBILITY_BASE_URL, resource_name)
    return get_resource(url)


def get_ar_servicepoint_resource(resource_name=None):
    template_vars = [
        ACCESSIBILITY_BASE_URL,
        getattr(settings, "ACCESSIBILITY_SYSTEM_ID", ""),
    ]
    url_template = "{}servicepoints/{}"
    if resource_name:
        template_vars.append(resource_name)
        url_template += "/{}"

    url = url_template.format(*template_vars)
    return get_resource(url)


def get_municipality_name_by_point(point):
    """
    Returns the string name of the municipality in which the point
    is located.
    """
    try:
        muni_type = AdministrativeDivisionType.objects.get(type="muni")
    except AdministrativeDivisionType.DoesNotExist:
        return None
    try:
        # resolve in which division the point is.
        division = AdministrativeDivisionGeometry.objects.get(
            division__type=muni_type, boundary__contains=point
        )
    except AdministrativeDivisionGeometry.DoesNotExist:
        return None
    # Get the division and return its name.
    return AdministrativeDivision.objects.get(id=division.division_id).name


def get_ar_servicepoint_accessibility_resource(resource_name=None):
    template_vars = [
        ACCESSIBILITY_BASE_URL,
        getattr(settings, "ACCESSIBILITY_SYSTEM_ID", ""),
    ]
    url_template = "{}accessibility/servicepoints/{}"
    if resource_name:
        template_vars.append(resource_name)
        url_template += "/{}"

    url = url_template.format(*template_vars)
    return get_resource(url)


def get_turku_resource(resource_name):
    url = "{}{}".format(TURKU_BASE_URL, resource_name)
    headers = get_turku_api_headers()
    return get_resource(url, headers)


def set_tku_translated_field(
    obj, obj_field_name, entry_data, max_length=None, clean=True
):
    if not entry_data:
        return False

    has_changed = False

    for language, raw_value in entry_data.items():
        if clean:
            value = clean_text(raw_value)
        else:
            value = raw_value

        if max_length and value and len(value) > max_length:
            value = None

        obj_key = "{}_{}".format(obj_field_name, language)
        obj_value = getattr(obj, obj_key)

        if obj_value == value:
            continue

        has_changed = True
        setattr(obj, obj_key, value)

    if has_changed:
        obj._changed = True

    return has_changed


def set_field(obj, obj_field_name, entry_value):
    value = clean_text(entry_value)
    obj_value = getattr(obj, obj_field_name)

    if obj_value == value:
        return False

    setattr(obj, obj_field_name, value)
    return True


def set_service_names_field(obj):
    service_names_fi = []
    service_names_sv = []
    service_names_en = []
    for service in obj.services.all():
        if service.name_fi:
            service_names_fi.append(service.name_fi)
        if service.name_sv:
            service_names_sv.append(service.name_sv)
        if service.name_en:
            service_names_en.append(service.name_en)

    if (
        obj.service_names_fi == service_names_fi
        and obj.service_names_sv == service_names_sv
        and obj.service_names_en == service_names_en
    ):
        return False

    setattr(obj, "service_names_fi", service_names_fi)
    setattr(obj, "service_names_sv", service_names_sv)
    setattr(obj, "service_names_en", service_names_en)
    return True


def set_syncher_service_names_field(obj):
    obj._changed |= set_service_names_field(obj)


def set_syncher_object_field(obj, obj_field_name, value):
    obj._changed |= set_field(obj, obj_field_name, value)


def set_syncher_tku_translated_field(
    obj, obj_field_name, value, max_length=None, clean=True
):
    obj._changed |= set_tku_translated_field(
        obj, obj_field_name, value, max_length, clean
    )


def postcodes():
    path = os.path.join(settings.BASE_DIR, "data", "fi", "postcodes.txt")
    _postcodes = {}
    f = open(path, "r", encoding="utf-8")
    for line in f.readlines():
        code, muni = line.split(",")
        _postcodes[code] = muni.strip()
    return _postcodes


def get_weekday_str(index, lang="fi"):
    assert 1 <= index <= 7 and lang in ("fi", "sv", "en")
    weekdays = (
        ("ma", "mån", "Mon"),
        ("ti", "tis", "Tue"),
        ("ke", "ons", "Wed"),
        ("to", "tor", "Thu"),
        ("pe", "fre", "Fri"),
        ("la", "lör", "Sat"),
        ("su", "sön", "Sun"),
    )
    return weekdays[index - 1][["fi", "sv", "en"].index(lang)]


def get_localized_value(data, preferred_language="fi"):
    assert preferred_language in ("fi", "sv", "en")
    return data.get(preferred_language) or ""


def convert_code_to_int(code):
    if code:
        return int.from_bytes(code.encode(), "big")
    return None


@lru_cache(None)
def get_municipality(name):
    try:
        return Municipality.objects.get(name=name)
    except Municipality.DoesNotExist:
        return None


def get_turku_boundary():
    division_turku = AdministrativeDivision.objects.filter(name="Turku").first()
    if division_turku:
        turku_boundary = AdministrativeDivisionGeometry.objects.get(
            division=division_turku
        ).boundary
        turku_boundary.transform(settings.DEFAULT_SRID)
        return turku_boundary
    else:
        return None


def create_service_node(service_node_id, name, parent_name, service_node_names):
    """
    Creates service_node with given name and id if it does not exist.
    Sets the parent service_node and name fields.
    :param service_node_id: the id of the service_node to be created.
    :param name: name of the service_node.
    :param parent_name: name of the parent service_node, if None the service_node will be
     topmost in the tree hierarchy.
    :param service_node_names: dict with names in all languages
    """
    service_node = None
    try:
        service_node = ServiceNode.objects.get(id=service_node_id, name=name)
    except ServiceNode.DoesNotExist:
        service_node = ServiceNode(id=service_node_id)

    if parent_name:
        try:
            parent = ServiceNode.objects.get(name=parent_name)
        except ServiceNode.DoesNotExist:
            raise ObjectDoesNotExist(
                "Parent ServiceNode name: {} not found.".format(parent_name)
            )
    else:
        # The service_node will be topmost in the tree structure
        parent = None

    service_node.parent = parent
    set_tku_translated_field(service_node, "name", service_node_names)
    service_node.last_modified_time = datetime.datetime.now(UTC_TIMEZONE)
    service_node.save()


def create_service(service_id, service_node_id, service_name, service_names):
    """
    Creates service with given service_id and name if it does not exist.
    Adds the service to the given service_node and sets the name fields.
    :param service_id: the id of the service.
    :param service_node_id: the id of the service_node to which the service will have a relation
    :param service_name: name of the service
    :param service_names: dict with names in all languages
    """
    service = None
    try:
        service = Service.objects.get(id=service_id, name=service_name)
    except Service.DoesNotExist:
        service = Service(
            id=service_id, clarification_enabled=False, period_enabled=False
        )
        set_tku_translated_field(service, "name", service_names)
        service_node = ServiceNode(id=service_node_id)
        service_node.related_services.add(service_id)
        service.last_modified_time = datetime.datetime.now(UTC_TIMEZONE)
        service.save()


@db.transaction.atomic
def delete_external_source(
    service_id,
    service_node_id,
    mobile_units_content_type_name,
):
    """
    Deletes the data source from services list and optionally from mobility_data.
    """
    Unit.objects.filter(services__id=service_id).delete()
    Service.objects.filter(id=service_id).delete()
    ServiceNode.objects.filter(id=service_node_id).delete()
    delete_mobile_units(mobile_units_content_type_name)
    update_service_node_counts()
    update_service_counts()


class BaseExternalSource:
    def __init__(self, config):
        self.config = config
        self.SERVICE_ID = config["service"]["id"]
        self.SERVICE_NODE_ID = config["service_node"]["id"]
        self.UNITS_ID_OFFSET = config["units_offset"]
        self.SERVICE_NAME = config["service"]["name"]["fi"]
        self.SERVICE_NAMES = config["service"]["name"]
        self.SERVICE_NODE_NAME = config["service_node"]["name"]["fi"]
        self.SERVICE_NODE_NAMES = config["service_node"]["name"]
        self.delete_external_source()
        create_service_node(
            self.config["service_node"]["id"],
            self.config["service_node"]["name"]["fi"],
            self.config["root_service_node_name"],
            self.config["service_node"]["name"],
        )
        create_service(
            self.config["service"]["id"],
            self.config["service_node"]["id"],
            self.config["service"]["name"]["fi"],
            self.config["service"]["name"],
        )

    def delete_external_source(self):
        delete_external_source(
            self.config["service"]["id"],
            self.config["service_node"]["id"],
            self.config["mobility_data_content_type_name"],
        )

    @db.transaction.atomic
    def save_objects_as_units(self, objects, content_type):
        for i, object in enumerate(objects):
            unit_id = i + self.UNITS_ID_OFFSET
            unit = Unit(id=unit_id)
            set_field(unit, "location", object.geometry)
            set_tku_translated_field(unit, "name", object.name)
            set_tku_translated_field(unit, "street_address", object.address)
            if hasattr(object, "description"):
                set_tku_translated_field(unit, "description", object.description)
            if hasattr(object, "extra"):
                set_field(unit, "extra", object.extra)
            if "provider_type" in self.config:
                set_syncher_object_field(
                    unit, "provider_type", self.config["provider_type"]
                )
            try:
                service = Service.objects.get(id=self.SERVICE_ID)
            except Service.DoesNotExist:
                self.logger.warning(
                    'Service "{}" does not exist!'.format(self.SERVICE_ID)
                )
                continue
            UnitServiceDetails.objects.get_or_create(unit=unit, service=service)
            service_nodes = ServiceNode.objects.filter(related_services=service)
            unit.service_nodes.add(*service_nodes)
            set_field(unit, "root_service_nodes", unit.get_root_service_nodes()[0])
            if hasattr(object, "municipality"):
                municipality = get_municipality(object.municipality)
                set_field(unit, "municipality", municipality)

            if hasattr(object, "address_zip"):
                set_field(unit, "address_zip", object.address_zip)
            unit.last_modified_time = datetime.datetime.now(UTC_TIMEZONE)
            set_service_names_field(unit)
            unit.save()
            if self.config.get("create_mobile_units_with_unit_reference", False):
                create_mobile_unit_as_unit_reference(unit_id, content_type)
        update_service_node_counts()
        update_service_counts()
        self.logger.info(f"Imported {len(objects)} {self.config['name']}...")
