import json
import os
from django.conf import settings
from django.contrib.gis.geos import Point
from munigeo.models import Municipality

from smbackend_turku.importers.utils import get_weekday_str


def create_municipality():
    Municipality.objects.create(
        id="turku", name="Turku", name_fi="Turku", name_sv="Åbo"
    )


def get_test_resource(resource_name):
    """
     Mock calling the API by fetching dummy data from files.
    """
    data_path = os.path.join(os.path.dirname(__file__), "data")
    if resource_name == "palvelut":
        file = os.path.join(data_path, "services.json")
    elif resource_name == "palveluluokat":
        file = os.path.join(data_path, "service_nodes.json")
    elif resource_name == "accessibility/variables":
        file = os.path.join(data_path, "accessibility_variables.json")
    elif resource_name == "properties":
        file = os.path.join(data_path, "accessibility_unit_properties.json")
    elif resource_name == "info":
        file = os.path.join(data_path, "accessibility_unit_info.json")
    else:
        file = os.path.join(data_path, "units.json")

    with open(file) as f:
        data = json.load(f)
    return data


def format_time(time_str):
    if not time_str:
        return ""
    parts = time_str.split(":")[:2]
    parts[0] = str(int(parts[0]))
    return ":".join(parts)


def get_opening_hours(opening_time, closing_time, weekday):
    opening_time = format_time(opening_time)
    closing_time = format_time(closing_time)
    weekday_str = "–".join(
        [get_weekday_str(int(wd), "fi") if wd else "" for wd in weekday.split("-")]
    )
    return "{} {}–{}".format(weekday_str, opening_time, closing_time)


def get_location(latitude, longitude, srid):
    point = Point(x=float(latitude), y=float(longitude), srid=srid)
    point.transform(settings.DEFAULT_SRID)
    return point
