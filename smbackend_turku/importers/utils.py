import datetime
import hashlib
import os
import re
import requests
import pytz
from functools import lru_cache
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from munigeo.models import (
    Municipality,
)

from services.models import (
    Service,
    ServiceNode,
)

# TODO: Change to production endpoint when available
TURKU_BASE_URL = "https://digiaurajoki.turku.fi:9443/kuntapalvelut/api/v1/"
ACCESSIBILITY_BASE_URL = "https://asiointi.hel.fi/kapaesteettomyys/api/v1/"
UTC_TIMEZONE = pytz.timezone("UTC")


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
