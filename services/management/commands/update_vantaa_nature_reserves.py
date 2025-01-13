import logging

import restapi
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.core.management import BaseCommand
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)
from munigeo.utils import get_default_srid

logger = logging.getLogger("services.management")

SRC_SERVICE_URL = "https://matti.vantaa.fi/server2/rest/services/Hosted/Luonnonsuojelualueet_rest/FeatureServer"
SRC_LAYER_NAME = "Luonnonsuojelualueet_rest"
SRC_SRID = 4326

OCD_ID_BASE = "ocd-division/country:fi/kunta:vantaa/luonnonsuojelualue:"


class Command(BaseCommand):
    help = "Update Vantaa nature reserves from Vantaa ArcGIS Server."

    def handle(self, *args, **options):
        self.update_nature_reserves()

    def get_features(self):
        service = restapi.FeatureService(SRC_SERVICE_URL)
        nature_reserves = service.layer(SRC_LAYER_NAME)
        return nature_reserves.query()

    def get_multi_geom(self, obj):
        if isinstance(obj, Polygon):
            return MultiPolygon(obj)
        elif isinstance(obj, (MultiPolygon)):
            return obj
        else:
            raise Exception(f"Unsupported geometry type: {obj.__class__.__name__}")

    def update_nature_reserves(self):
        num_nature_reserves_updated = 0

        src_srs = SpatialReference(SRC_SRID)
        dest_srs = SpatialReference(get_default_srid())
        src_to_dest = CoordTransform(src_srs, dest_srs)

        municipality = Municipality.objects.get(name_fi="Vantaa")
        division_type = AdministrativeDivisionType.objects.get(type="nature_reserve")

        features = self.get_features()

        logger.info("Found {} nature reserves for Vantaa".format(features.count))
        logger.info("Importing nature reserves...")

        updated_nature_reserves = []
        for feature in features:
            props = feature.get("properties")
            source_id = props.get("objectid_1")
            name_fi = props.get("nimi")
            geometry = feature.get("geometry")

            if not geometry:
                logger.warning(f"Nature reserve {name_fi} has no geometry, skipping")
                continue

            geom = self.get_multi_geom(GEOSGeometry(str(geometry), srid=SRC_SRID))
            geom.transform(src_to_dest)

            defaults = {
                "name_fi": name_fi,
                "type": division_type,
                "origin_id": source_id,
                "municipality": municipality,
            }

            division, _ = AdministrativeDivision.objects.update_or_create(
                ocd_id=OCD_ID_BASE + str(source_id),
                defaults=defaults,
            )
            AdministrativeDivisionGeometry.objects.update_or_create(
                division=division,
                defaults={"boundary": geom},
            )
            logger.debug("Updated nature reserve {}".format(division.name_fi))
            updated_nature_reserves.append(division)
            num_nature_reserves_updated += 1

        # Delete nature reserves that are no longer in the source data
        all_nature_reserves = AdministrativeDivision.objects.filter(
            type=division_type,
            municipality=municipality,
        )
        deleted_nature_reserves = all_nature_reserves.exclude(
            id__in=[division.id for division in updated_nature_reserves]
        )
        num_nature_reserves_deleted = deleted_nature_reserves.delete()[0]
        logger.info(
            f"Import completed. {num_nature_reserves_updated} nature reserves updated"
            f" and {num_nature_reserves_deleted} deleted."
        )
