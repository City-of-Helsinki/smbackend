import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import LineString

from mobility_data.models import ContentType, MobileUnit

from .utils import delete_mobile_units, get_or_create_content_type

BRUSH_SALTED_BICYCLE_NETWORK_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Harjasuolatut_pyoratiet&outputFormat=GML3",
)
BRUSH_SANDED_BICYCLE_NETWORK_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Harjahiekoitetut_pyoratiet&outputFormat=GML3",
)

SOURCE_DATA_SRID = 3877
logger = logging.getLogger("mobility_data")


@db.transaction.atomic
def delete_brush_salted_bicycle_network():
    delete_mobile_units(ContentType.BRUSH_SALTED_BICYCLE_NETWORK)


@db.transaction.atomic
def delete_brush_sanded_bicycle_network():
    delete_mobile_units(ContentType.BRUSH_SANDED_BICYCLE_NETWORK)


@db.transaction.atomic
def create_brush_salted_bicycle_network_content_type():
    description = "Brush salted bicycle network In the region of Turku"
    name = "Brush salted bicycle network"
    content_type, _ = get_or_create_content_type(
        ContentType.BRUSH_SALTED_BICYCLE_NETWORK, name, description
    )
    return content_type


@db.transaction.atomic
def create_brush_sanded_bicycle_network_content_type():
    description = "Brush sanded bicycle network In the region of Turku"
    name = "Brush sanded bicycle network"
    content_type, _ = get_or_create_content_type(
        ContentType.BRUSH_SANDED_BICYCLE_NETWORK, name, description
    )
    return content_type


def get_geometry_objects(layer):
    geometries = []
    for feature in layer:
        geom = feature.geom
        geom.transform(settings.DEFAULT_SRID)
        geometries.append(LineString(geom.coords, srid=settings.DEFAULT_SRID))
    return geometries


@db.transaction.atomic
def import_brush_salted_bicycle_network(delete=True):
    if delete:
        delete_brush_salted_bicycle_network()
    ds = DataSource(BRUSH_SALTED_BICYCLE_NETWORK_URL)
    assert len(ds) == 1
    geometries = get_geometry_objects(ds[0])
    content_type = create_brush_salted_bicycle_network_content_type()
    for geometry in geometries:
        MobileUnit.objects.create(content_type=content_type, geometry=geometry)


@db.transaction.atomic
def import_brush_sanded_bicycle_network(delete=True):
    if delete:
        delete_brush_sanded_bicycle_network()
    ds = DataSource(BRUSH_SANDED_BICYCLE_NETWORK_URL)
    assert len(ds) == 1
    geometries = get_geometry_objects(ds[0])
    content_type = create_brush_sanded_bicycle_network_content_type()
    for geometry in geometries:
        MobileUnit.objects.create(content_type=content_type, geometry=geometry)
