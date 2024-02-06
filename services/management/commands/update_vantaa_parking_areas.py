"""
This management command updates Vantaa parking areas.
"""

import logging
import os
from time import time

from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, LineString, MultiPolygon, Polygon
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
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/kadunvarsipysakointi-alue:",
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
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/raskaanliikenteen-pysakointipaikka-alue:",
    },
    {
        "type": "hgv_street_parking_area",
        "service_url": "https://matti.vantaa.fi/server2/rest/services/Hosted/Raskaan_liikenteen_sallitut_kadunvarret/"
        "FeatureServer",
        "layer_name": "Raskaan liikenteen sallitut kadunvarret MUOKATTAVA",
        "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/raskaanliikenteen-sallittu-kadunvarsi-alue:",
    },
]

SRC_SRID = 4326

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

    def get_multi_geom(self, obj):
        """
        Return the appropriate multi-container for the supplied geometry.
        If the geometry is already a multi-container, return the object itself.
        """
        if isinstance(obj, Polygon):
            return MultiPolygon(obj)
        elif isinstance(obj, (MultiPolygon)):
            return obj
        elif isinstance(obj, (LineString)):
            buffered_line = self.transform_line_to_polygon(obj)
            if isinstance(buffered_line, MultiPolygon):
                return buffered_line
            elif isinstance(buffered_line, Polygon):
                return MultiPolygon([buffered_line])
            else:
                raise ValueError("Buffered geometry is not a Polygon or MultiPolygon.")
        else:
            raise Exception(
                "Unsupported geometry type: {}".format(obj.__class__.__name__)
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
            features = parking_areas.query()

            readable_name = data_source["type"].replace("_", " ").strip() + "s"
            logger.info(f"Found {features.count} {readable_name} for Vantaa")
            logger.info(f"Importing {readable_name}...")

            updated_parking_areas = []
            for feature in features:
                geom = self.get_multi_geom(
                    GEOSGeometry(str(feature.get("geometry")), srid=SRC_SRID)
                )
                geom.transform(src_to_dest)
                props = feature.get("properties")
                origin_id = (
                    str(props.get("objectid")) if props.get("objectid") else None
                )
                if not origin_id:
                    logger.warning("Parking area has no origin ID, skipping")
                    continue
                name_fi = props.get("tyyppi")
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
                logger.debug("Updated parking area {}".format(division.name_fi))
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
                f"Import completed. {num_parking_areas_updated} {readable_name} updated and {num_parking_areas_deleted}"
                f" deleted in {time() - start_time:.0f} seconds."
            )
