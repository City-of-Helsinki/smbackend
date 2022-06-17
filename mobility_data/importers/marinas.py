"""
Imports marinas, guest marina and boat parking.
"""
import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.models import ContentType, MobileUnit

from .utils import delete_mobile_units, get_or_create_content_type

# NOTE, TODO, when the data is available in the public WFS server, change the URLS
# MARINA_URL = "{}{}".format(
#     settings.TURKU_WFS_URL,
#     "?service=WFS&request=GetFeature&typeName=GIS:Venesatamat&outputFormat=GML3"
# )
# GUEST_MARINA_BOAT_PARKING_URL = "{}{}".format(
#     settings.TURKU_WFS_URL,
#     "service=WFS&request=GetFeature&typeName=GIS:Muu_venesatama&outputFormat=GML3"
# )

MARINA_URL = (
    "http://tkuikp/TeklaOGCWeb/WFS.ashx?"
    "service=WFS&request=GetFeature&typeName=GIS:Venesatamat&outputFormat=GML3"
)
GUEST_MARINA_BOAT_PARKING_URL = (
    "http://tkuikp/TeklaOGCWeb/WFS.ashx?"
    "service=WFS&request=GetFeature&typeName=GIS:Muu_venesatama&outputFormat=GML3"
)

GUEST_MARINA = "Vierasvenesatama"
BOAT_PARKING = "Lyhytaikainen veneparkki"
SOURCE_DATA_SRID = 3877
logger = logging.getLogger("mobility_data")


class Marina:
    def __init__(self, feature):
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.name = feature["Venesatamat"].as_string()


@db.transaction.atomic
def delete_guest_marina():
    delete_mobile_units(ContentType.GUEST_MARINA)


db.transaction.atomic


def create_guest_marina_content_type():
    description = "Guest marina in Turku."
    name = "Guest marina"
    content_type, _ = get_or_create_content_type(
        ContentType.GUEST_MARINA, name, description
    )
    return content_type


@db.transaction.atomic
def delete_boat_parking():
    delete_mobile_units(ContentType.BOAT_PARKING)


db.transaction.atomic


def create_boat_parking_content_type():
    description = "Boat parking in Turku."
    name = "Boat parking"
    content_type, _ = get_or_create_content_type(
        ContentType.BOAT_PARKING, name, description
    )
    return content_type


@db.transaction.atomic
def delete_marinas():
    delete_mobile_units(ContentType.MARINA)


db.transaction.atomic


def create_marina_content_type():
    description = "Marinas in the Turku region."
    name = "Marina"
    content_type, _ = get_or_create_content_type(ContentType.MARINA, name, description)
    return content_type


@db.transaction.atomic
def import_marinas(delete=True):
    marinas = []
    if delete:
        delete_marinas()

    ds = DataSource(MARINA_URL)
    for feature in ds[0]:
        marinas.append(Marina(feature))
    content_type = create_marina_content_type()
    for marina in marinas:
        MobileUnit.objects.create(
            content_type=content_type, geometry=marina.geometry, name=marina.name
        )
    return len(marinas)


@db.transaction.atomic
def import_guest_marina_and_boat_parking(delete=True):
    """
    The data for the guest marina and the boat parking comes from the same
    WFS feature. They are recognized by the value of the field "Muu_venesatama".
    """
    if delete:
        delete_guest_marina()
        delete_boat_parking()
    ds = DataSource(GUEST_MARINA_BOAT_PARKING_URL)
    for feature in ds[0]:
        geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        geometry.transform(settings.DEFAULT_SRID)
        type_name = feature["Muu_venesatama"].as_string()
        content_type = None
        if type_name == GUEST_MARINA:
            content_type = create_guest_marina_content_type()
        elif type_name == BOAT_PARKING:
            content_type = create_boat_parking_content_type()

        MobileUnit.objects.create(content_type=content_type, geometry=geometry)
