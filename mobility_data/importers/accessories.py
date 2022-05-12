"""
Imports features from layer GIS:varusteet.
Features importer are: benches, public toilets, tables and furniture
groups.
"""
import logging
from collections import namedtuple

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_or_create_content_type,
    locates_in_turku,
)
from mobility_data.models import ContentType
from mobility_data.models.mobile_unit import MobileUnit

logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 3877

ACCESSORIES_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Varusteet&outputFormat=GML3&maxFeatures=10000",
)
PUBLIC_TOILET = "WC"
BENCH = "Penkki"
TABLE = "Poyta"
FURNITURE_GROUP = "Kalusteryhma"


class Accessory:
    def __init__(self, feature):
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra = {}
        self.extra["type_code"] = feature["Varustelaji_koodi"].as_int()
        self.extra["manufacturer"] = feature["Valmistaja"].as_string()
        self.extra["manufacturer_code"] = feature["Valmistaja_koodi"].as_int()
        self.extra["model"] = feature["Malli"].as_string()
        self.extra["model_code"] = feature["Malli_koodi"].as_int()
        self.extra["year_of_acquisition"] = feature["Hankintavuosi"].as_int()
        self.extra["condition"] = feature["Kunto"].as_string()
        self.extra["condition_code"] = feature["Kunto_koodi"].as_string()
        self.extra["surface_area"] = feature["Pinta-ala"].as_string()
        self.extra["length"] = feature["Pituus"].as_double()
        self.extra["installation"] = feature["Asennus"].as_string()
        self.extra["installation_code"] = feature["Asennus_koodi"].as_string()


def get_accessory_objects():
    ds = DataSource(ACCESSORIES_URL)
    layer = ds[0]
    public_toilets = []
    tables = []
    benches = []
    furniture_groups = []
    for feature in layer:
        if not locates_in_turku(feature, SOURCE_DATA_SRID):
            continue
        type_name = feature["Tyyppi"].as_string()
        if not type_name:
            continue
        if type_name in PUBLIC_TOILET:
            public_toilets.append(Accessory(feature))
        elif type_name in BENCH:
            benches.append(Accessory(feature))
        elif type_name in TABLE:
            tables.append(Accessory(feature))
        elif type_name in FURNITURE_GROUP:
            furniture_groups.append(Accessory(feature))
    Accesories = namedtuple(
        "Accessories", ["public_toilets", "benches", "tables", "furniture_groups"]
    )
    return Accesories(public_toilets, benches, tables, furniture_groups)


@db.transaction.atomic
def create_public_toilet_content_type():
    description = "Public toilets in the Turku region."
    name = "Public toilets"
    content_type, _ = get_or_create_content_type(
        ContentType.ACCESSORY_PUBLIC_TOILET, name, description
    )
    return content_type


@db.transaction.atomic
def create_table_content_type():
    description = "Tables in the Turku region."
    name = "Tables"
    content_type, _ = get_or_create_content_type(
        ContentType.ACCESSORY_TABLE, name, description
    )
    return content_type


@db.transaction.atomic
def create_bench_content_type():
    description = "Benches in the Turku region."
    name = "Benches"
    content_type, _ = get_or_create_content_type(
        ContentType.ACCESSORY_BENCH, name, description
    )
    return content_type


@db.transaction.atomic
def create_furniture_group_content_type():
    description = "Furniture groups in the Turku region."
    name = "Furniture groups"
    content_type, _ = get_or_create_content_type(
        ContentType.ACCESSORY_FURNITURE_GROUP, name, description
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
        mobile_unit.extra = object.extra
        mobile_unit.save()


def get_accessory_elements():
    return {
        "public toilets": {
            "objects_field_name": "public_toilets",
            "content_type": ContentType.ACCESSORY_PUBLIC_TOILET,
            "create_content_type_func": create_public_toilet_content_type,
        },
        "benches": {
            "objects_field_name": "benches",
            "content_type": ContentType.ACCESSORY_BENCH,
            "create_content_type_func": create_bench_content_type,
        },
        "tables": {
            "objects_field_name": "tables",
            "content_type": ContentType.ACCESSORY_TABLE,
            "create_content_type_func": create_table_content_type,
        },
        "furniture groups": {
            "objects_field_name": "furniture_groups",
            "content_type": ContentType.ACCESSORY_FURNITURE_GROUP,
            "create_content_type_func": create_furniture_group_content_type,
        },
    }
