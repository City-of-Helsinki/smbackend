import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.models import ContentType, MobileUnit

from .utils import delete_mobile_units, get_or_create_content_type

PAAVONPOLKU_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Paavonpolut&outputFormat=GML3",
)
SOURCE_DATA_SRID = 3877
logger = logging.getLogger("mobility_data")


class Paavonpolku:
    def __init__(self, feature):
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.name = feature["Tunnus"].as_string()
        self.extra = {"length": feature["Pituus"].as_string()}


@db.transaction.atomic
def delete_paavonpolkus():
    delete_mobile_units(ContentType.PAAVONPOLKU)


@db.transaction.atomic
def create_paavonpolku_content_type():
    description = "Paavonpolku routes in the Turku region."
    name = "Paavonpolku"
    content_type, _ = get_or_create_content_type(
        ContentType.PAAVONPOLKU, name, description
    )
    return content_type


@db.transaction.atomic
def import_paavonpolkus(delete=True):
    paavonpolkus = []
    if delete:
        delete_paavonpolkus()

    ds = DataSource(PAAVONPOLKU_URL)
    assert len(ds) == 1
    for feature in ds[0]:
        paavonpolkus.append(Paavonpolku(feature))
    content_type = create_paavonpolku_content_type()
    for paavonpolku in paavonpolkus:
        MobileUnit.objects.create(
            content_type=content_type,
            geometry=paavonpolku.geometry,
            name=paavonpolku.name,
            extra=paavonpolku.extra,
        )
    return len(paavonpolkus)
