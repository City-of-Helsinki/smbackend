import logging

from django import db
from django.conf import settings
from django.contrib.gis.geos import Point

from mobility_data.models import MobileUnit

from .utils import delete_mobile_units, fetch_json, get_or_create_content_type

URL = "http://data.foli.fi/gtfs/stops"
CONTENT_TYPE_NAME = "FoliStop"
logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 4326


class FoliStop:
    def __init__(self, stop_data):
        self.extra = {}
        self.name = stop_data["stop_name"]
        lon = stop_data["stop_lon"]
        lat = stop_data["stop_lat"]
        self.geometry = Point(lon, lat, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra["stop_code"] = stop_data["stop_code"]
        self.extra["wheelchair_boarding"] = stop_data["wheelchair_boarding"]


def get_foli_stops():
    json_data = fetch_json(URL)
    objects = []
    for stop_code in json_data:
        objects.append(FoliStop(json_data[stop_code]))
    return objects


@db.transaction.atomic
def get_and_create_foli_stop_content_type():
    description = "Föli stops."
    content_type, _ = get_or_create_content_type(CONTENT_TYPE_NAME, description)
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_mobile_units(CONTENT_TYPE_NAME)

    content_type = get_and_create_foli_stop_content_type()
    for object in objects:
        MobileUnit.objects.create(
            content_type=content_type,
            name=object.name,
            geometry=object.geometry,
            extra=object.extra,
        )
    logger.info(f"Saved {len(objects)} Föli stops to database.")
