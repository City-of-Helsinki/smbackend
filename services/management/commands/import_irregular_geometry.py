import json
import os

from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management import BaseCommand

from services.models import Unit
from services.models.unit import PROJECTION_SRID


def import_area():
    data_path = os.path.join(settings.BASE_DIR, "data")
    file = os.path.join(data_path, "geometry/koirametsa.geojson")
    with open(file, "r") as geojson_file:
        geojson_data = json.load(geojson_file)

    geom_str = json.dumps(geojson_data["features"][0]["geometry"])
    geom = GEOSGeometry(geom_str)
    multi_polygon = MultiPolygon([geom])

    src_srs = SpatialReference(3879)
    target_srs = SpatialReference(PROJECTION_SRID)
    transform = CoordTransform(src_srs, target_srs)
    multi_polygon.transform(transform)

    unit = Unit.objects.get(id=23795)  # Östersundomin koirametsä
    unit.geometry = multi_polygon
    unit.save()


class Command(BaseCommand):
    help = "Import area data for Östersundomin koirametsä (unit id 23795)."

    def handle(self, *args, **options):
        import_area()
