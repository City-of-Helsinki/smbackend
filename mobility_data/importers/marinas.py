"""
Imports marinas, guest marina and boat parking.
Note, wfs importer is not used as the berths data is
separately assigned to the marina mobile units.
"""
import logging

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry

from .berths import get_berths
from .utils import MobileUnitDataBase

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


class MarinaBase(MobileUnitDataBase):
    def __init__(self, feature):
        super().__init__()
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)


class Marina(MarinaBase):
    def __init__(self, feature):
        super().__init__(feature)
        self.name["fi"] = feature["Venesatamat"].as_string()
        berths = get_berths(self.name)
        self.extra = {"berths": berths}


class GuestMarina(MarinaBase):
    def __init__(self, feature):
        super().__init__(feature)


class BoatParking(MarinaBase):
    def __init__(self, feature):
        super().__init__(feature)


def get_marinas():
    marinas = []
    ds = DataSource(MARINA_URL)
    for feature in ds[0]:
        marinas.append(Marina(feature))
    return marinas


def get_guest_marinas():
    guest_marinas = []
    ds = DataSource(GUEST_MARINA_BOAT_PARKING_URL)
    for feature in ds[0]:
        type_name = feature["Muu_venesatama"].as_string()
        if type_name == GUEST_MARINA:
            guest_marinas.append(GuestMarina(feature))
    return guest_marinas


def get_boat_parkings():
    boat_parkings = []
    ds = DataSource(GUEST_MARINA_BOAT_PARKING_URL)
    for feature in ds[0]:
        type_name = feature["Muu_venesatama"].as_string()
        if type_name == BOAT_PARKING:
            boat_parkings.append(BoatParking(feature))
    return boat_parkings
