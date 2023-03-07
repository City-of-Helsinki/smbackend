from django import db
from django.conf import settings
from django.contrib.gis.geos import Point
from munigeo.models import Municipality

from mobility_data.models import MobileUnit

from .utils import (
    delete_mobile_units,
    fetch_json,
    get_or_create_content_type_from_config,
    set_translated_field,
)

URL = "https://data.foli.fi/geojson/poi"
FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME = "FoliParkAndRideCarsStop"
FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME = "FoliParkAndRideBikesStop"
PARKANDRIDE_CARS = "PARKANDRIDE_CARS"
PARKANDRIDE_BIKES = "PARKANDRIDE_BIKES"
SOURCE_DATA_SRID = 4326


class ParkAndRideStop:
    def __init__(self, feature):
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
        self.description = properties["text"]
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


def get_parkandride_stop_objects():
    json_data = fetch_json(URL)
    car_stops = []
    bike_stops = []
    for feature in json_data["features"]:
        if feature["properties"]["category"] == PARKANDRIDE_CARS:
            car_stops.append(ParkAndRideStop(feature))
        elif feature["properties"]["category"] == PARKANDRIDE_BIKES:
            bike_stops.append(ParkAndRideStop(feature))

    return car_stops, bike_stops


@db.transaction.atomic
def save_to_database(objects, content_type_name, delete_tables=True):
    assert (
        content_type_name == FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME
        or content_type_name == FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME
    )
    if delete_tables:
        delete_mobile_units(content_type_name)

    content_type = get_or_create_content_type_from_config(content_type_name)

    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            geometry=object.geometry,
            address_zip=object.address_zip,
            description=object.description,
            municipality=object.municipality,
        )
        mobile_unit.content_types.add(content_type)
        set_translated_field(mobile_unit, "name", object.name)
        set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.save()

    return len(objects)
