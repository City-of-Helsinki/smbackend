import json
import os

from django.conf import settings
from django.contrib.gis.geos import Point


def get(api_client, url, data=None):
    response = api_client.get(url, data=data, format="json")
    assert response.status_code == 200, str(response.content)
    return response


def get_test_resource(resource_name):
    """
    Mock calling the API by fetching dummy data from files.
    """
    data_path = os.path.join(os.path.dirname(__file__), "data")
    if resource_name == "entrances":
        file = os.path.join(data_path, "unit_entrances.json")
    else:
        return None

    with open(file) as f:
        data = json.load(f)
    return data


def get_test_location(latitude, longitude, srid):
    point = Point(x=float(latitude), y=float(longitude), srid=srid)
    point.transform(settings.DEFAULT_SRID)
    return point
