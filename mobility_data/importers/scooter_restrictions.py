import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.models import ContentType, MobileUnit

from .utils import delete_mobile_units, get_or_create_content_type

PARKING_ZONE_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Sahkopotkulautaparkki&outputFormat=GML3",
)
SPEED_LIMIT_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Sahkopotkulauta_nopeusrajoitus&outputFormat=GML3",
)
NO_PARKING_ZONE_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Sahkopotkulauta_pysakointikielto&outputFormat=GML3",
)
PARKING_ZONE_TEST_DATA = "scooter_parkings.gml"
SPEED_LIMIT_TEST_DATA = "scooter_speed_limits.gml"
NO_PARKING_ZONE_TEST_DATA = "scooter_no_parking_zones.gml"

SOURCE_DATA_SRID = 3877
logger = logging.getLogger("mobility_data")


class ScooterRestriction:
    def __init__(self, feature):
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)


def get_datasource_layer(url):
    ds = DataSource(url)
    layer = ds[0]
    return layer


def get_restriction_objects(layer):
    objects = []
    for feature in layer:
        objects.append(ScooterRestriction(feature))
    return objects


@db.transaction.atomic
def create_scooter_parking_content_type():
    description = "Scooter parking zones in the Turku region."
    name = "Scooter parking"
    content_type, _ = get_or_create_content_type(
        ContentType.SCOOTER_PARKING, name, description
    )
    return content_type


@db.transaction.atomic
def create_scooter_speed_limit_content_type():
    description = "Scooter speed limit zones in the Turku region."
    name = "Scooter speed limit"
    content_type, _ = get_or_create_content_type(
        ContentType.SCOOTER_SPEED_LIMIT, name, description
    )
    return content_type


@db.transaction.atomic
def create_scooter_speed_no_parking_content_type():
    description = "Scooter no parking zones in the Turku region."
    name = "Scooter no parking"
    content_type, _ = get_or_create_content_type(
        ContentType.SCOOTER_NO_PARKING, name, description
    )
    return content_type


@db.transaction.atomic
def save_to_database(objects, create_content_type_func, content_type_str, delete=True):
    if delete:
        delete_mobile_units(content_type_str)
    content_type = create_content_type_func()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(content_type=content_type)
        mobile_unit.geometry = object.geometry
        mobile_unit.save()


def get_scooter_restriction_elements():
    return {
        "Parking": {
            "url": PARKING_ZONE_URL,
            "content_type": ContentType.SCOOTER_PARKING,
            "content_type_create_func": create_scooter_parking_content_type,
            "test_data": PARKING_ZONE_TEST_DATA,
        },
        "Speed Limit": {
            "url": SPEED_LIMIT_URL,
            "content_type": ContentType.SCOOTER_SPEED_LIMIT,
            "content_type_create_func": create_scooter_speed_limit_content_type,
            "test_data": SPEED_LIMIT_TEST_DATA,
        },
        "No Parking": {
            "url": NO_PARKING_ZONE_URL,
            "content_type": ContentType.SCOOTER_NO_PARKING,
            "content_type_create_func": create_scooter_speed_no_parking_content_type,
            "test_data": NO_PARKING_ZONE_TEST_DATA,
        },
    }
