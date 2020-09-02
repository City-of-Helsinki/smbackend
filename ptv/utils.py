import pytz
import requests

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
