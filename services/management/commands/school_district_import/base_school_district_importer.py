import logging

from django.contrib.gis.gdal import CoordTransform, DataSource, SpatialReference
from django.contrib.gis.geos import MultiPolygon
from munigeo.models import AdministrativeDivisionGeometry, Municipality

from services.management.commands.lipas_import import MiniWFS

logger = logging.getLogger(__name__)
SRID = 3067


class BaseSchoolDistrictImporter:
    """
    Shared functionality for importing school districts from a WFS source.

    Subclasses must define ``WFS_BASE`` and ``MUNICIPALITY_ID`` and implement
    ``import_districts``.
    """

    WFS_BASE = None
    MUNICIPALITY_ID = None

    def __init__(self, district_type=None):
        self.district_type = district_type

    def get_municipality(self):
        return Municipality.objects.get(id=self.MUNICIPALITY_ID)

    def fetch_layer(self, source_type):
        wfs = MiniWFS(self.WFS_BASE)
        datasource_resource = None

        try:
            url = wfs.get_feature(type_name=source_type)
            datasource_input, datasource_resource = self.prepare_datasource_input(url)
            layer = DataSource(datasource_input)[0]
            layer._datasource_resource = datasource_resource
        except Exception as e:
            if datasource_resource is not None:
                datasource_resource.cleanup()
            logger.exception(f"Error retrieving data for {source_type}: {e}")
            raise

        logger.info(f"Retrieved {len(layer)} {source_type} features.")
        logger.info("Processing data...")
        return layer

    def prepare_datasource_input(self, url):
        return url, None

    def import_districts(self, data):
        raise NotImplementedError

    @staticmethod
    def save_geometry(feature, division):
        geom = feature.geom
        if not geom.srid:
            geom.srid = SRID
        if geom.srid != SRID:
            geom.transform(SRID)
            ct = CoordTransform(SpatialReference(geom.srid), SpatialReference(SRID))
            geom.transform(ct)

        geom = geom.geos
        if geom.geom_type == "Polygon":
            geom = MultiPolygon(geom.buffer(0), srid=geom.srid)

        try:
            geom_obj = division.geometry
        except AdministrativeDivisionGeometry.DoesNotExist:
            geom_obj = AdministrativeDivisionGeometry(division=division)

        geom_obj.boundary = geom
        geom_obj.save()
