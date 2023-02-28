import os
import re

import requests
from django.conf import settings
from django.utils.http import urlencode

URL_BASE = "https://www.hel.fi/palvelukarttaws/rest/v4/"

LATIN_1_CHARS = (
    (b"\xe2\x80\x99", b"'"),
    (b"\xc3\xa9", b"e"),
    (b"\xe2\x80\x90", b"-"),
    (b"\xe2\x80\x91", b"-"),
    (b"\xe2\x80\x92", b"-"),
    (b"\xe2\x80\x93", b"-"),
    (b"\xe2\x80\x94", b"-"),
    (b"\xe2\x80\x94", b"-"),
    (b"\xe2\x80\x98", b"'"),
    (b"\xe2\x80\x9b", b"'"),
    (b"\xe2\x80\x9c", b'"'),
    (b"\xe2\x80\x9c", b'"'),
    (b"\xe2\x80\x9d", b'"'),
    (b"\xe2\x80\x9e", b'"'),
    (b"\xe2\x80\x9f", b'"'),
    (b"\xe2\x80\xa6", b"..."),
    (b"\xe2\x80\xb2", b"'"),
    (b"\xe2\x80\xb3", b"'"),
    (b"\xe2\x80\xb4", b"'"),
    (b"\xe2\x80\xb5", b"'"),
    (b"\xe2\x80\xb6", b"'"),
    (b"\xe2\x80\xb7", b"'"),
    (b"\xe2\x81\xba", b"+"),
    (b"\xe2\x81\xbb", b"-"),
    (b"\xe2\x81\xbc", b"="),
    (b"\xe2\x81\xbd", b"("),
    (b"\xe2\x81\xbe", b")"),
)


def clean_latin1(data):
    try:
        return data.encode("ISO-8859-1").decode("UTF-8")
    except UnicodeEncodeError:
        unicode_data = data.encode("UTF-8")
        for _hex, _char in LATIN_1_CHARS:
            unicode_data = unicode_data.replace(_hex, _char)
        return unicode_data.decode("UTF-8")


def pk_get(resource_name, res_id=None, params=None):
    url = "%s%s/" % (URL_BASE, resource_name)
    if res_id is not None:
        url = "%s%s/" % (url, res_id)
    if params:
        url += "?" + urlencode(params)
    print("CALLING URL >>> ", url)
    resp = requests.get(url, timeout=300)
    assert resp.status_code == 200, "fuu status code {}".format(resp.status_code)
    return resp.json()


def save_translated_field(obj, obj_field_name, info, info_field_name, max_length=None):
    has_changed = False
    for lang in ("fi", "sv", "en"):
        key = "%s_%s" % (info_field_name, lang)
        if key in info:
            val = clean_text(info[key])
        else:
            val = None
        if max_length and val and len(val) > max_length:
            val = None
        obj_key = "%s_%s" % (obj_field_name, lang)
        obj_val = getattr(obj, obj_key)
        if obj_val == val:
            continue

        if getattr(obj, obj_key) != val:
            setattr(obj, obj_key, val)
            has_changed = True
        if lang == "fi":
            setattr(obj, obj_field_name, val)
    return has_changed


def clean_text(text):
    if not isinstance(text, str):
        return text
    text = text.replace("\r\n", "\n")
    # remove consecutive whitespaces
    text = re.sub(r"[ \t][ \t]+", " ", text, re.U)
    # remove nil bytes
    text = text.replace("\u0000", " ")
    text = text.replace("\r", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\\r", "\n")
    text = text.strip()
    if len(text) == 0:
        return None
    return text


def update_service_names_fields(obj, info, obj_changed, update_fields):
    service_names_fi = []
    service_names_sv = []
    service_names_en = []
    for service in obj.services.all():
        service_names_fi.append(service.name_fi)
        service_names_sv.append(service.name_sv)
        service_names_en.append(service.name_en)

    if (
        obj.service_names_fi == service_names_fi
        and obj.service_names_sv == service_names_sv
        and obj.service_names_en == service_names_en
    ):
        return obj_changed, update_fields

    setattr(obj, "service_names_fi", service_names_fi)
    setattr(obj, "service_names_sv", service_names_sv)
    setattr(obj, "service_names_en", service_names_en)
    update_fields.extend(["service_names_fi", "service_names_sv", "service_names_en"])
    obj_changed = True
    return obj_changed, update_fields


def convert_to_list(text):
    return [e.strip() for e in text.split(",")]


def get_extra_searchwords(info, language):
    field_name = "extra_searchwords_%s" % language
    val = info.get(field_name, [])
    if val:
        val = convert_to_list(val)
    return val


def update_extra_searchwords(obj, info, obj_changed, update_fields):
    extra_searchwords_fi = get_extra_searchwords(info, "fi")
    extra_searchwords_sv = get_extra_searchwords(info, "sv")
    extra_searchwords_en = get_extra_searchwords(info, "en")
    if (
        obj.extra_searchwords_fi == extra_searchwords_fi
        and obj.extra_searchwords_sv == extra_searchwords_sv
        and obj.extra_searchwords_en == extra_searchwords_en
    ):
        return obj_changed, update_fields

    if extra_searchwords_fi:
        setattr(obj, "extra_searchwords_fi", extra_searchwords_fi)
        update_fields.append("extra_searchwords_fi")
    if extra_searchwords_sv:
        setattr(obj, "extra_searchwords_sv", extra_searchwords_sv)
        update_fields.append("extra_searchwords_sv")
    if extra_searchwords_en:
        setattr(obj, "extra_searchwords_en", extra_searchwords_en)
        update_fields.append("extra_searchwords_en")
    obj_changed = True
    return obj_changed, update_fields


def postcodes():
    path = os.path.join(settings.BASE_DIR, "data", "fi", "postcodes.txt")
    postcodes = {}
    f = open(path, "r", encoding="utf-8")
    for line in f.readlines():
        code, muni = line.split(",")
        postcodes[code] = muni.strip()
    return postcodes
