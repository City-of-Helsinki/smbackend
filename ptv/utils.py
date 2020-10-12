import pytz
import requests
from django.conf import settings
from django.db.models import Max

PTV_BASE_URL = "https://api.palvelutietovaranto.suomi.fi/api/v11/"

UTC_TIMEZONE = pytz.timezone("UTC")


def get_ptv_resource(area_code, resource_name=None, page=1):
    if resource_name == "service":
        endpoint = "Service/list/area/Municipality/code/"
    else:
        endpoint = "ServiceChannel/list/area/Municipality/code/"

    url = "{}{}{}?page={}".format(PTV_BASE_URL, endpoint, area_code, page)
    print("CALLING URL >>> ", url)
    resp = requests.get(url)
    assert resp.status_code == 200, "status code {}".format(resp.status_code)
    return resp.json()


def create_available_id(model, increment=0):
    """
    Create an id by getting next available id since AutoField is not in use.
    "Reserve" first 10 000 id's for Turku data, so they can be kept the same as they are in the original source.
    Not a pretty solution so probably need to TODO: rethink the id system when more than one data source is in use.
    """
    new_id = (model.objects.aggregate(Max("id"))["id__max"] or 0) + increment
    if "smbackend_turku" in settings.INSTALLED_APPS:
        buffer = settings.TURKU_ID_BUFFER
        if new_id < buffer:
            new_id += buffer
    return new_id
