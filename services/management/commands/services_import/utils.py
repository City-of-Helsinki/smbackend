import re
import os
import requests
from django.conf import settings
from django.utils.http import urlencode

from services.models import Keyword

URL_BASE = 'http://www.hel.fi/palvelukarttaws/rest/v4/'
SUPPORTED_LANGUAGES = ['fi', 'sv', 'en']


def pk_get(resource_name, res_id=None, params=None):
    url = "%s%s/" % (URL_BASE, resource_name)
    if res_id is not None:
        url = "%s%s/" % (url, res_id)
    if params:
        url += '?' + urlencode(params)
    print("CALLING URL >>> ", url)
    resp = requests.get(url)
    assert resp.status_code == 200, 'fuu status code {}'.format(resp.status_code)
    return resp.json()


def save_translated_field(obj, obj_field_name, info, info_field_name, max_length=None):
    has_changed = False
    for lang in ('fi', 'sv', 'en'):
        key = '%s_%s' % (info_field_name, lang)
        if key in info:
            val = clean_text(info[key])
        else:
            val = None
        if max_length and val and len(val) > max_length:
            # if self.verbosity:
            #     self.logger.warning("%s: field '%s' too long" % (obj, obj_field_name))
            val = None
        obj_key = '%s_%s' % (obj_field_name, lang)
        obj_val = getattr(obj, obj_key, None)
        if obj_val == val:
            continue

        setattr(obj, obj_key, val)
        if lang == 'fi':
            setattr(obj, obj_field_name, val)
        has_changed = True
    return has_changed


def clean_text(text):
    if not isinstance(text, str):
        return text
    # remove consecutive whitespaces
    text = re.sub(r'\s\s+', ' ', text, re.U)
    # remove nil bytes
    text = text.replace('\u0000', ' ')
    text = text.replace("\r", "\n")
    text = text.replace('\r', "\n")
    text = text.replace('\\r', "\n")
    text = text.strip()
    if len(text) == 0:
        return None
    return text


def postcodes():
    path = os.path.join(settings.BASE_DIR, 'data', 'fi', 'postcodes.txt')
    postcodes = {}
    f = open(path, 'r', encoding='utf-8')
    for l in f.readlines():
        code, muni = l.split(',')
        postcodes[code] = muni.strip()
    return postcodes


def keywords():
    keywords = {}
    for lang in SUPPORTED_LANGUAGES:
        kw_list = Keyword.objects.filter(language=lang)
        kw_dict = {kw.name: kw for kw in kw_list}
        keywords[lang] = kw_dict
    return keywords


def keywords_by_id(keywords):
    return {kw.pk: kw for kw in Keyword.objects.all()}
