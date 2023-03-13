from django.conf import settings
from django.contrib.gis.geos import Point
from munigeo.models import Municipality

from .utils import fetch_json, MobileUnitDataBase

URL = "https://data.foli.fi/geojson/poi"
FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME = "FoliParkAndRideCarsStop"
FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME = "FoliParkAndRideBikesStop"
PARKANDRIDE_CARS = "PARKANDRIDE_CARS"
PARKANDRIDE_BIKES = "PARKANDRIDE_BIKES"
SOURCE_DATA_SRID = 4326


class ParkAndRideStop(MobileUnitDataBase):
    def __init__(self, feature):
        super().__init__()
        properties = feature["properties"]
        self.name = {
            "fi": properties["name_fi"],
            "sv": properties["name_sv"],
            "en": properties["name_en"],
        }
        self.address = {
            "fi": properties["address_fi"],
            "sv": properties["address_sv"],
            "en": properties["address_fi"],
        }
        self.address_zip = properties["text"].split(" ")[-1]
        self.description["fi"] = properties["text"]
        try:
            self.municipality = Municipality.objects.get(name=properties["city"])
        except Municipality.DoesNotExist:
            self.municipality = None
        geometry = feature["geometry"]
        self.geometry = Point(
            geometry["coordinates"][0],
            geometry["coordinates"][1],
            srid=SOURCE_DATA_SRID,
        )
        self.geometry.transform(settings.DEFAULT_SRID)


def get_parkandride_car_stop_objects():
    json_data = fetch_json(URL)
    car_stops = []
    for feature in json_data["features"]:
        if feature["properties"]["category"] == PARKANDRIDE_CARS:
            car_stops.append(ParkAndRideStop(feature))
    return car_stops


def get_parkandride_bike_stop_objects():
    json_data = fetch_json(URL)
    bike_stops = []
    for feature in json_data["features"]:
        if feature["properties"]["category"] == PARKANDRIDE_BIKES:
            bike_stops.append(ParkAndRideStop(feature))
    return bike_stops
