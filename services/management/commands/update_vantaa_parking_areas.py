"""
This management command updates Vantaa parking areas.
"""

import logging
import os
from itertools import batched
from time import time

from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import (
    GEOSGeometry,
    LineString,
    MultiLineString,
    MultiPolygon,
    Polygon,
)
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

DATA_SOURCES = [
    {
        "type": "parking_area",
        "service_url": "https://matti.vantaa.fi/server2/rest/services/Hosted/Pys%C3%A4k%C3%B6intialueet/FeatureServer",
        "layer_name": "Pysäköintialueet MUOKATTAVA",
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/pysakointipaikka-alue:",
    },
    {
        "type": "street_parking_area",
        "service_url": "https://matti.vantaa.fi/server2/rest/services/Hosted/Kadunvarsipys%C3%A4k%C3%B6inti/"
        "FeatureServer",
        "layer_name": "Kadunvarsipysäköinti MUOKATTAVA",
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/kadunvarsipysakointi-alue:",  # noqa: E501
    },
    {
        "type": "park_and_ride_area",
        "service_url": "https://matti.vantaa.fi/server2/rest/services/Hosted/Liitynt%C3%A4pys%C3%A4k%C3%B6intialueet/"
        "FeatureServer",
        "layer_name": "Liityntäpysäköintialueet MUOKATTAVA",
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/liityntapysakointi-alue:",
    },
    {
        "type": "hgv_parking_area",
        "service_url": "https://matti.vantaa.fi/server2/rest/services/Hosted/Raskaan_liikenteen_"
        "pys%C3%A4k%C3%B6intialueet/FeatureServer",
        "layer_name": "Raskaan liikenteen pysäköintialueet MUOKATTAVA",
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/raskaanliikenteen-pysakointipaikka-alue:",  # noqa: E501
    },
    {
        "type": "hgv_street_parking_area",
        "service_url": "https://matti.vantaa.fi/server2/rest/services/Hosted/Raskaan_liikenteen_sallitut_kadunvarret/"
        "FeatureServer",
        "layer_name": "Raskaan liikenteen sallitut kadunvarret MUOKATTAVA",
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/raskaanliikenteen-sallittu-kadunvarsi-alue:",  # noqa: E501
    },
    {
        "type": "hgv_no_parking_area",
        "service_url": "https://matti.vantaa.fi/server2/rest/services/Hosted/Raskaan_liikenteen_kielletyt_kadunvarret/"
        "FeatureServer",
        "layer_name": "Raskaan liikenteen kielletyt kadunvarret MUOKATTAVA",
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/raskaanliikenteen-kielletty-kadunvarsi-alue:",  # noqa: E501
    },
]

SRC_SRID = 4326
BATCH_SIZE = 1000

PARKING_NAME_TRANSLATIONS = {
    "12h-24h": {"sv": "12-24 timmar", "en": "12-24 hours"},
    "2h-3h": {"sv": "2-3 timmar", "en": "2-3 hours"},
    "4h-11h": {"sv": "4-11 timmar", "en": "4-11 hours"},
    "Ei rajoitusta": {"sv": "Ingen begränsning", "en": "No limitation"},
    "Lyhytaikainen": {"sv": "Kortvarig", "en": "Temporary"},
    "Maksullinen": {"sv": "Avgiftsbelagd", "en": "Paid"},
    "Muu": {"sv": "Något annat", "en": "Other"},
    "Varattu päivisin": {"sv": "Bokas dagtid", "en": "Reserved during the day"},
    "Liityntäpysäköinti": {"sv": "Pendelparkering", "en": "Park & Ride"},
}


class UnsupportedGeometryError(Exception):
    pass


class Command(BaseCommand):
    help = "Update Vantaa parking areas from Vantaa ArcGIS Server"

    def handle(self, *args, **options) -> None:
        self.update_parking_areas()

    def transform_line_to_polygon(self, obj):
        """
        Transform a LineString to a Polygon or MultiPolygon.
        """
        target_srid = (
            32633  # UTM zone 33N (with UTM we can use meters to buffer the line)
        )
        original_spatial_ref = SpatialReference(obj.srid)
        target_spatial_ref = SpatialReference(target_srid)
        coord_transform = CoordTransform(original_spatial_ref, target_spatial_ref)
        transformed_line = obj.transform(coord_transform, clone=True)

        # Buffer the line with 1 meter to create a polygon
        buffered_line = transformed_line.buffer(1)

        # Transform the buffered geometry back to the original SRID
        if obj.srid != target_srid:
            back_transform = CoordTransform(target_spatial_ref, original_spatial_ref)
            buffered_line.transform(back_transform)

        return buffered_line

    def _convert_polygon_to_multi(self, polygon):
        """Convert a Polygon to MultiPolygon preserving SRID."""
        multi_poly = MultiPolygon(polygon)
        multi_poly.srid = polygon.srid
        return multi_poly

    def _convert_linestring_to_multi(self, linestring):
        """Convert a LineString to MultiPolygon by buffering."""
        buffered = self.transform_line_to_polygon(linestring)
        if isinstance(buffered, MultiPolygon):
            return buffered
        if isinstance(buffered, Polygon):
            return self._convert_polygon_to_multi(buffered)
        raise ValueError("Buffered geometry is not a Polygon or MultiPolygon.")

    def _convert_multilinestring_to_multi(self, multilinestring):
        """Convert a MultiLineString to MultiPolygon by buffering each line."""
        polygons = []
        for line in multilinestring:
            buffered = self.transform_line_to_polygon(line)
            if not isinstance(buffered, (Polygon, MultiPolygon)):
                raise ValueError("Buffered geometry is not a Polygon or MultiPolygon.")

            # If buffered is a MultiPolygon, extract individual Polygons
            if isinstance(buffered, MultiPolygon):
                polygons.extend(list(buffered))
            else:
                polygons.append(buffered)

        multi_poly = MultiPolygon(polygons)
        multi_poly.srid = multilinestring.srid
        return multi_poly

    def get_multi_geom(self, obj):
        """
        Return the appropriate multi-container for the supplied geometry.
        If the geometry is already a multi-container, return the object itself.
        """
        if isinstance(obj, MultiPolygon):
            return obj
        if isinstance(obj, Polygon):
            return self._convert_polygon_to_multi(obj)
        if isinstance(obj, LineString):
            return self._convert_linestring_to_multi(obj)
        if isinstance(obj, MultiLineString):
            return self._convert_multilinestring_to_multi(obj)

        raise UnsupportedGeometryError(
            f"Unsupported geometry type: {obj.__class__.__name__}"
        )

    def update_parking_areas(self):
        src_srs = SpatialReference(SRC_SRID)
        dest_srs = SpatialReference(get_default_srid())
        src_to_dest = CoordTransform(src_srs, dest_srs)
        municipality = Municipality.objects.get(name_fi="Vantaa")

        for data_source in DATA_SOURCES:
            start_time = time()
            num_parking_areas_updated = 0

            try:
                division_type = AdministrativeDivisionType.objects.get(
                    type=data_source["type"]
                )
            except AdministrativeDivisionType.DoesNotExist:
                division_name = (
                    data_source["layer_name"].replace("MUOKATTAVA", "").strip()
                )
                division_type = AdministrativeDivisionType.objects.create(
                    type=data_source["type"], name=division_name
                )

            service = restapi.FeatureService(data_source["service_url"])
            parking_areas = service.layer(data_source["layer_name"])

            # Retrieve all features using pagination to handle more than
            # the record limit
            features = []

            # First, get all object IDs
            all_oids_result = parking_areas.query(returnIdsOnly=True)

            # Extract object IDs from the result
            if hasattr(all_oids_result, "objectIds"):
                all_oids = all_oids_result.objectIds
            elif isinstance(all_oids_result, dict) and "objectIds" in all_oids_result:
                all_oids = all_oids_result["objectIds"]
            else:
                # Fallback: try to query all features at once
                logger.warning(
                    "Could not retrieve object IDs, "
                    "attempting to query all features at once"
                )
                features = parking_areas.query()
                all_oids = []

            # Query features in batches using object IDs
            if all_oids:
                all_features = []

                for batch_oids in batched(all_oids, BATCH_SIZE):
                    oid_string = ",".join(map(str, batch_oids))
                    batch = parking_areas.query(objectIds=oid_string)
                    if batch:
                        all_features.extend(batch)

                features = all_features

            readable_name = data_source["type"].replace("_", " ").strip() + "s"
            logger.info(f"Found {len(features)} {readable_name} for Vantaa")
            logger.info(f"Importing {readable_name}...")

            updated_parking_areas = []
            for feature in features:
                geometry = feature.get("geometry")
                props = feature.get("properties")
                name_fi = props.get("tyyppi")

                if not geometry:
                    logger.warning(f"Parking area {name_fi} has no geometry, skipping")
                    continue
                geom = self.get_multi_geom(GEOSGeometry(str(geometry), srid=SRC_SRID))
                geom.transform(src_to_dest)

                origin_id = (
                    str(props.get("objectid")) if props.get("objectid") else None
                )
                if not origin_id:
                    logger.warning("Parking area has no origin ID, skipping")
                    continue
                defaults = {
                    "name_fi": name_fi,
                    "municipality": municipality,
                    "type": division_type,
                    "extra": props,
                    "origin_id": origin_id,
                }
                try:
                    name_en = PARKING_NAME_TRANSLATIONS[name_fi]["en"]
                    name_sv = PARKING_NAME_TRANSLATIONS[name_fi]["sv"]
                    defaults["name_en"] = name_en
                    defaults["name_sv"] = name_sv
                except KeyError:
                    logger.warning(f"No translation for {name_fi}")

                division, _ = AdministrativeDivision.objects.update_or_create(
                    ocd_id=data_source["ocd_id_base"] + origin_id,
                    defaults=defaults,
                )
                AdministrativeDivisionGeometry.objects.update_or_create(
                    division=division,
                    defaults={"boundary": geom},
                )
                logger.debug(f"Updated parking area {division.name_fi}")
                updated_parking_areas.append(division)
                num_parking_areas_updated += 1

            # Delete parking areas that are no longer in the source data
            all_parking_areas = AdministrativeDivision.objects.filter(
                type=division_type, municipality=municipality
            )
            removed_parking_areas = all_parking_areas.exclude(
                id__in=[area.id for area in updated_parking_areas]
            )
            num_parking_areas_deleted = removed_parking_areas.delete()[0]

            logger.info(
                f"Import completed. {num_parking_areas_updated} {readable_name} updated"
                f" and {num_parking_areas_deleted} deleted in"
                f" {time() - start_time:.0f} seconds."
            )
