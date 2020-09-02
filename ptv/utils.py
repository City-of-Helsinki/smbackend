import pytz
import requests

PTV_BASE_URL = "https://api.palvelutietovaranto.suomi.fi/api/v11/"

UTC_TIMEZONE = pytz.timezone("UTC")


def get_ptv_resource(area_code):
    url = "{}{}{}".format(
        PTV_BASE_URL, "ServiceChannel/list/area/Municipality/code/", area_code
    )
    print("CALLING URL >>> ", url)
    resp = requests.get(url)
    assert resp.status_code == 200, "status code {}".format(resp.status_code)
    return resp.json()
