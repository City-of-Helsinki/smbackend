import logging

from django.contrib.gis.gdal import DataSource
from django.core.management import BaseCommand
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

from services.management.commands.lipas_import import get_multi, MiniWFS, WFS_BASE

logger = logging.getLogger(__name__)

TYPES = {
    "paths": "lipas:lipas_112_muu_luonnonsuojelualue",
}

VANTAA_MUNI_ID = 92

OCD_ID_BASE = "ocd-division/country:fi/kunta:vantaa/luonnonsuojelualue:"


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.import_vantaa_nature_reserves()

    def import_vantaa_nature_reserves(self):
        logger.info("Retrieving Vantaa nature reserves from Lipas...")

        municipality = Municipality.objects.get(name_fi="Vantaa")
        try:
            division_type = AdministrativeDivisionType.objects.get(
                type="nature_reserve"
            )
        except AdministrativeDivisionType.DoesNotExist:
            division_type = AdministrativeDivisionType.objects.create(
                type="nature_reserve", name="Luonnonsuojelualue"
            )

        wfs = MiniWFS(WFS_BASE)
        layers = {}
        for key, val in TYPES.items():
            url = wfs.get_feature(
                type_name=val, cql_filter=f"kuntanumero={VANTAA_MUNI_ID}"
            )
            layers[key] = DataSource(url)[0]
            logger.info(f"Retrieved {len(layers[key])} features.")

        logger.info("Processing Lipas geodata...")
        num_nature_reserves_updated = 0
        updated_nature_reserves = []
        for layer in layers.values():
            for feature in layer:
                lipas_id = feature["id"].value
                name_fi = feature["nimi_fi"].value
                geometry = get_multi(feature.geom.geos)

                defaults = {
                    "name_fi": name_fi,
                    "type": division_type,
                    "origin_id": lipas_id,
                    "municipality": municipality,
                }

                division, _ = AdministrativeDivision.objects.update_or_create(
                    ocd_id=OCD_ID_BASE + str(lipas_id),
                    defaults=defaults,
                )
                AdministrativeDivisionGeometry.objects.update_or_create(
                    division=division,
                    defaults={"boundary": geometry},
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
            f"Import completed. {num_nature_reserves_updated} nature reserves updated and "
            f"{num_nature_reserves_deleted} deleted."
        )
