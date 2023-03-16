import logging

from django.conf import settings
from django.contrib.gis.geos import Point

from .utils import fetch_json, MobileUnitDataBase

URL = "http://data.foli.fi/gtfs/stops"
CONTENT_TYPE_NAME = "FoliStop"
logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 4326


class FoliStop(MobileUnitDataBase):
    def __init__(self, stop_data):
        super().__init__()
        self.name["fi"] = stop_data["stop_name"]
        lon = stop_data["stop_lon"]
        lat = stop_data["stop_lat"]
        self.geometry = Point(lon, lat, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra["stop_code"] = stop_data["stop_code"]
        self.extra["wheelchair_boarding"] = stop_data["wheelchair_boarding"]


def get_foli_stops():
    json_data = fetch_json(URL)
    return [FoliStop(json_data[stop_code]) for stop_code in json_data]
