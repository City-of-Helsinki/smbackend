import logging
from time import time

import restapi
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management.base import BaseCommand
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)
from munigeo.utils import get_default_srid

logger = logging.getLogger("services.management")

OCD_ID_VANTAA_PARKING_PAYZONE_BASE = (
    "ocd-division/country:fi/kunta:vantaa/pysakointimaksuvyohyke:"
)

SRC_SERVICE_URL = "https://matti.vantaa.fi/server2/rest/services/Hosted/Maksuvy%C3%B6hykkeet/FeatureServer"
SRC_LAYER_NAME = "Maksuvyöhykkeet MUOKATTAVA"
SRC_SRID = 4326

PAYZONE_TRANSLATIONS = {
    "1 € / tunti": {"sv": "1 € / timme", "en": "1 € / hour"},
    "2 € / tunti": {"sv": "2 € / timme", "en": "2 € / hour"},
}


class Command(BaseCommand):
    help = "Update Vantaa parking payzones from Vantaa ArcGIS Server."

    def handle(self, *args, **options) -> None:
        self.update_parking_payzones()

    def get_features(self):
        service = restapi.FeatureService(SRC_SERVICE_URL)
        parking_payzones = service.layer(SRC_LAYER_NAME)
        return parking_payzones.query()

    def update_parking_payzones(self):
        start_time = time()
        num_parking_payzones_updated = 0

        src_srs = SpatialReference(SRC_SRID)
        dest_srs = SpatialReference(get_default_srid())
        src_to_dest = CoordTransform(src_srs, dest_srs)

        municipality = Municipality.objects.get(name_fi="Vantaa")
        division_type = AdministrativeDivisionType.objects.get(type="parking_payzone")

        features = self.get_features()

        logger.info("Found {} parking payzones for Vantaa".format(features.count))
        logger.info("Importing parking payzones...")

        updated_parking_payzones = []
        for feature in features:
            props = feature.get("properties")
            name_fi = props.get("maksullisu")
            geometry = feature.get("geometry")

            if not geometry:
                logger.warning(f"Parking payzone {name_fi} has no geometry, skipping")
                continue

            geom = MultiPolygon(GEOSGeometry(str(geometry), srid=SRC_SRID))
            geom.transform(src_to_dest)

            origin_id = str(props.get("objectid")) if props.get("objectid") else None
            if not origin_id:
                logger.warning("Parking payzone has no origin ID, skipping")
                continue

            defaults = {
                "name_fi": name_fi,
                "municipality": municipality,
                "type": division_type,
                "extra": props,
                "origin_id": origin_id,
            }

            try:
                name_en = PAYZONE_TRANSLATIONS[name_fi]["en"]
                name_sv = PAYZONE_TRANSLATIONS[name_fi]["sv"]
                defaults["name_en"] = name_en
                defaults["name_sv"] = name_sv
            except KeyError:
                logger.warning(f"No translation for {name_fi}")

            division, _ = AdministrativeDivision.objects.update_or_create(
                ocd_id=OCD_ID_VANTAA_PARKING_PAYZONE_BASE + origin_id,
                defaults=defaults,
            )
            AdministrativeDivisionGeometry.objects.update_or_create(
                division=division,
                defaults={"boundary": geom},
            )
            logger.debug("Updated parking payzone {}".format(division.name_fi))

            updated_parking_payzones.append(division)
            num_parking_payzones_updated += 1

        # Delete parking payzones that are no longer in the source data
        all_parking_payzones = AdministrativeDivision.objects.filter(
            type=division_type, municipality=municipality
        )
        removed_parking_payzones = all_parking_payzones.exclude(
            id__in=[zone.id for zone in updated_parking_payzones]
        )
        num_parking_payzones_deleted = removed_parking_payzones.delete()[0]

        logger.info(
            f"Import completed. {num_parking_payzones_updated} parking payzones updated and "
            f"{num_parking_payzones_deleted} deleted in {time() - start_time:.0f} seconds."
        )
