import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_file_name_from_data_source,
    get_or_create_content_type_from_config,
    get_root_dir,
    set_translated_field,
)
from mobility_data.models import MobileUnit

logger = logging.getLogger("bicycle_network")
SOURCE_DATA_SRID = 3877
GEOJSON_FILENAME = "Yhteiskayttoautojen_pysakointi_2022.geojson"

LANGUAGES = [language[0] for language in settings.LANGUAGES]
CONTENT_TYPE_NAME = "ShareCarParkingPlace"


class CarShareParkingPlace:
    RESTRICTION_FIELD = "Rajoit_lis"
    EXCLUDE_FIELDS = ["id", "Osoite", RESTRICTION_FIELD]
    CAR_PARKING_NAME = {
        "fi": "Yhteiskäyttöautojen pysäköintipaikka",
        "sv": "Bilpoolbilars parkeringsplats",
        "en": "Parking place for car sharing cars",
    }

    def __init__(self, feature):
        self.name = {}
        self.extra = {}
        self.address = {}
        street_name = {}
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)

        for field in feature.fields:
            if field not in self.EXCLUDE_FIELDS:
                self.extra[field] = feature[field].as_string()

        address_fi, address_sv = [
            address.strip() for address in feature["Osoite"].as_string().split("/")
        ]
        restrictions = feature[self.RESTRICTION_FIELD].as_string().split("/")

        street_name["fi"] = address_fi.split(",")[0]
        street_name["sv"] = address_sv.split(",")[0]
        street_name["en"] = street_name["fi"]
        self.extra[self.RESTRICTION_FIELD] = {}
        for i, language in enumerate(LANGUAGES):
            self.name[
                language
            ] = f"{self.CAR_PARKING_NAME[language]}, {street_name[language]}"
            self.address[language] = street_name[language]
            self.extra[self.RESTRICTION_FIELD][language] = restrictions[i].strip()


def get_car_share_parking_place_objects(geojson_file=None):
    car_share_parking_places = []
    file_name = None
    if not geojson_file:
        file_name = get_file_name_from_data_source(CONTENT_TYPE_NAME)
        if not file_name:
            file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    else:
        # Use the test data file
        file_name = f"{get_root_dir()}/mobility_data/tests/data/{geojson_file}"

    data_layer = GDALDataSource(file_name)[0]
    for feature in data_layer:
        car_share_parking_places.append(CarShareParkingPlace(feature))
    return car_share_parking_places


@db.transaction.atomic
def delete_car_share_parking_places():
    delete_mobile_units(CONTENT_TYPE_NAME)


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_car_share_parking_places()
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    for object in objects:
        mobile_unit = MobileUnit.objects.create(extra=object.extra)
        mobile_unit.content_types.add(content_type)
        set_translated_field(mobile_unit, "name", object.name)
        set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.save()
