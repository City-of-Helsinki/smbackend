import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_or_create_content_type,
)
from mobility_data.models import ContentType
from mobility_data.models.mobile_unit import MobileUnit

logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 3877

SPEED_LIMITS_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Nopeusrajoitusalueet&outputFormat=GML3&maxFeatures=10000",
)


class SpeedLimit:
    def __init__(self, feature):
        """
        The source data contains also polygons that marks areas inside the
        speed limit polygon that are not affected by the limit. This is made
        into a multipolygon where the first polygon is the speed limit itself
        and the rest of the polygons marks areas that are not affected by the
        speed limit.
        """
        if len(feature.geom.coords) > 1:
            polygons = []
            for coords in feature.geom.coords:
                polygons.append(Polygon(coords, srid=SOURCE_DATA_SRID))
            self.geometry = MultiPolygon(polygons, srid=SOURCE_DATA_SRID)
        else:
            self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.speed_limit = feature["Nopeus"].as_int()


def get_speed_limit_objects():
    ds = DataSource(SPEED_LIMITS_URL)
    layer = ds[0]
    objects = []
    for feature in layer:
        objects.append(SpeedLimit(feature))
    return objects


@db.transaction.atomic
def create_speed_limit_content_type():
    description = "Speed limit zones in the Turku region."
    name = "Speed limit zones"
    content_type, _ = get_or_create_content_type(
        ContentType.SPEED_LIMIT_ZONE, name, description
    )
    return content_type


@db.transaction.atomic
def delete_speed_limit_zones():
    delete_mobile_units(ContentType.SPEED_LIMIT_ZONE)


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_speed_limit_zones()
    content_type = create_speed_limit_content_type()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type,
        )
        extra = {"speed_limit": object.speed_limit}
        mobile_unit.geometry = object.geometry
        mobile_unit.extra = extra
        mobile_unit.save()
