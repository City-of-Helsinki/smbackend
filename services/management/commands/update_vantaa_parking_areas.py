"""
This management command updates Vantaa parking areas.
"""
import logging
import os
from time import time

from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management.base import BaseCommand
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)
from munigeo.utils import get_default_srid

os.environ["RESTAPI_USE_ARCPY"] = "FALSE"
os.environ["RESTAPI_VERIFY_CERT"] = "FALSE"
import restapi  # noqa: E402

logger = logging.getLogger("services.management")

OCD_ID_VANTAA_PARKING_BASE = (
    "ocd-division/country:fi/kunta:vantaa/pysakointipaikka-alue:"
)
SRC_SERVICE_URL = "https://matti.vantaa.fi/server2/rest/services/Hosted/Pys%C3%A4k%C3%B6intialueet/FeatureServer"
SRC_LAYER_NAME = "Pyskintialueet MUOKATTAVA"
SRC_SRID = 4326


class Command(BaseCommand):
    help = "Update Vantaa parking areas from Vantaa ArcGIS Server"

    def handle(self, *args, **options) -> None:
        self.update_parking_areas()

    def get_multi_geom(self, obj):
        """
        Return the appropriate multi-container for the supplied geometry.
        If the geometry is already a multi-container, return the object itself.
        """
        if isinstance(obj, Polygon):
            return MultiPolygon(obj)
        elif isinstance(obj, (MultiPolygon)):
            return obj
        else:
            raise Exception(
                "Unsupported geometry type: {}".format(obj.__class__.__name__)
            )

    def update_parking_areas(self):
        start_time = time()
        num_parking_areas_updated = 0

        src_srs = SpatialReference(SRC_SRID)
        dest_srs = SpatialReference(get_default_srid())
        src_to_dest = CoordTransform(src_srs, dest_srs)

        municipality = Municipality.objects.get(name_fi="Vantaa")
        type = AdministrativeDivisionType.objects.get(type="parking_area")

        service = restapi.FeatureService(SRC_SERVICE_URL)
        parking_areas = service.layer(SRC_LAYER_NAME)
        features = parking_areas.query()

        logger.info("Found {} parking areas for Vantaa".format(features.count))
        logger.info("Importing parking areas...")

        updated_parking_areas = []
        for feature in features:
            geom = self.get_multi_geom(
                GEOSGeometry(str(feature.get("geometry")), srid=SRC_SRID)
            )
            geom.transform(src_to_dest)
            props = feature.get("properties")
            origin_id = str(props.get("objectid")) if props.get("objectid") else None
            if not origin_id:
                logger.warning("Parking area has no origin ID, skipping")
                continue
            division, _ = AdministrativeDivision.objects.update_or_create(
                ocd_id=OCD_ID_VANTAA_PARKING_BASE + origin_id,
                defaults={
                    "name_fi": props.get("tyyppi"),
                    "municipality": municipality,
                    "type": type,
                    "extra": props,
                    "origin_id": origin_id,
                },
            )
            AdministrativeDivisionGeometry.objects.update_or_create(
                division=division,
                defaults={"boundary": geom},
            )
            logger.debug("Updated parking area {}".format(division.name_fi))
            updated_parking_areas.append(division)
            num_parking_areas_updated += 1

        # Delete parking areas that are no longer in the source data
        all_parking_areas = AdministrativeDivision.objects.filter(
            type=type, municipality=municipality
        )
        removed_parking_areas = all_parking_areas.exclude(
            id__in=[area.id for area in updated_parking_areas]
        )
        num_parking_areas_deleted = removed_parking_areas.delete()[0]

        logger.info(
            f"Import completed. {num_parking_areas_updated} parking areas updated and {num_parking_areas_deleted} deleted "
            f"in {time() - start_time:.0f} seconds."
        )
