"""
Imports marinas, guest marina and boat parking.
Note, wfs importer is not used as the berths data is
separately assigned to the marina mobile units.
"""
import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.models import MobileUnit

from .berths import get_berths
from .utils import delete_mobile_units, get_or_create_content_type_from_config

MARINA_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Venesatamat&outputFormat=GML3",
)
GUEST_MARINA_BOAT_PARKING_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Muu_venesatama&outputFormat=GML3",
)
GUEST_MARINA_CONTENT_TYPE_NAME = "GuestMarina"
BOAT_PARKING_CONTENT_TYPE_NAME = "BoatParking"
MARINA_CONTENT_TYPE_NAME = "Marina"

GUEST_MARINA = "Vierasvenesatama"
BOAT_PARKING = "Lyhytaikainen veneparkki"
SOURCE_DATA_SRID = 3877
logger = logging.getLogger("mobility_data")


class Marina:
    def __init__(self, feature):
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.name = feature["Venesatamat"].as_string()
        berths = get_berths(self.name)
        self.extra = {"berths": berths}


@db.transaction.atomic
def delete_guest_marina():
    delete_mobile_units(GUEST_MARINA_CONTENT_TYPE_NAME)



@db.transaction.atomic
def delete_boat_parking():
    delete_mobile_units(BOAT_PARKING_CONTENT_TYPE_NAME)


@db.transaction.atomic
def delete_marinas():
    delete_mobile_units(MARINA_CONTENT_TYPE_NAME)


@db.transaction.atomic
def import_marinas(delete=True):
    marinas = []
    if delete:
        delete_marinas()

    ds = DataSource(MARINA_URL)
    for feature in ds[0]:
        marinas.append(Marina(feature))
    content_type = get_or_create_content_type_from_config(MARINA_CONTENT_TYPE_NAME)
    for marina in marinas:
        mobile_unit = MobileUnit.objects.create(
            geometry=marina.geometry,
            name=marina.name,
            extra=marina.extra,
        )
        mobile_unit.content_types.add(content_type)
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
            content_type = get_or_create_content_type_from_config(GUEST_MARINA_CONTENT_TYPE_NAME)
        elif type_name == BOAT_PARKING:
            content_type = get_or_create_content_type_from_config(BOAT_PARKING_CONTENT_TYPE_NAME)

        mobile_unit = MobileUnit.objects.create(geometry=geometry)
        mobile_unit.content_types.add(content_type)
