import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import Polygon

from mobility_data.models import ContentType, MobileUnit

from .utils import delete_mobile_units, get_or_create_content_type

logger = logging.getLogger("mobility_data")
PAYMENT_ZONES_URL = "".format(
    settings.TURKU_WFS_URL,
    "service=WFS&request=GetFeature&typeName=GIS:Pysakoinnin_maksuvyohykkeet&outputFormat=GML3",
)
SOURCE_DATA_SRID = 3877


class PaymentZone:
    # These are the names of the data fields in the source data.
    FIELDS = [
        "Lisatieto",
        "maksullisuus_arki",
        "maksullisuus_lauantai",
        "maksullisuus_sunnuntai",
        "maksuvyohyke",
        "maksuvyohykehinta",
        "paatosdiaari",
        "paatospykala",
    ]
    geometry = None

    def __init__(self, feature):
        for field in self.FIELDS:
            setattr(self, field, feature[field].as_string())
        polygon = Polygon(feature.geom.coords[0], srid=SOURCE_DATA_SRID)
        polygon.transform(settings.DEFAULT_SRID)
        self.geometry = polygon


def get_payment_zone_objects():
    ds = DataSource(PAYMENT_ZONES_URL)
    layer = ds[0]
    payment_zones = []
    for feature in layer:
        payment_zones.append(PaymentZone(feature))
    return payment_zones


@db.transaction.atomic
def delete_payment_zones():
    delete_mobile_units(ContentType.PAYMENT_ZONE)


@db.transaction.atomic
def create_payment_zone_content_type():
    description = "Payment zones In the region of Turku"
    name = "Payment Zones"
    content_type, _ = get_or_create_content_type(
        ContentType.PAYMENT_ZONE, name, description
    )
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_payment_zones()

    content_type = create_payment_zone_content_type()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type,
        )
        extra = {}
        for field in PaymentZone.FIELDS:
            extra[field] = getattr(object, field, None)
        mobile_unit.extra = extra
        mobile_unit.geometry = object.geometry
        mobile_unit.save()
