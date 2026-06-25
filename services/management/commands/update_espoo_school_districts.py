import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from munigeo.models import AdministrativeDivision

from services.management.commands.school_district_import.espoo_school_district_importer import (  # noqa: E501
    EspooSchoolDistrictImporter,
)

logger = logging.getLogger(__name__)

MUNICIPALITY_ID = "espoo"

SCHOOL_DISTRICT_DATA = [
    {
        "source_type": "GIS:Oppilaaksiottoalueet_suomenkielinen",
        "division_type": "lower_comprehensive_school_district_fi",
        "ocd_id": "oppilaaksiottoalue_alakoulu_fi",
    },
    {
        "source_type": "GIS:Oppilaaksiottoalueet_suomenkielinen",
        "division_type": "upper_comprehensive_school_district_fi",
        "ocd_id": "oppilaaksiottoalue_ylakoulu_fi",
    },
    {
        "source_type": "GIS:Oppilaaksiottoalueet_ruotsinkielinen_ala_aste",
        "division_type": "lower_comprehensive_school_district_sv",
        "ocd_id": "oppilaaksiottoalue_alakoulu_sv",
    },
]

# Division types that are no longer imported but whose stale Espoo data must
# still be removed.
OBSOLETE_DIVISION_TYPES = [
    "upper_comprehensive_school_district_sv",
]


class Command(BaseCommand):
    help = "Update Espoo comprehensive school districts."

    @transaction.atomic
    def handle(self, *args, **options):
        importer = EspooSchoolDistrictImporter(district_type="school")

        # Group data by division type
        data_by_division_type = {}
        for data in SCHOOL_DISTRICT_DATA:
            data_by_division_type.setdefault(data["division_type"], []).append(data)

        for division_type, dataset in data_by_division_type.items():
            logger.info(f"Updating division type: {division_type}")
            try:
                with transaction.atomic():
                    # Remove old divisions before importing new ones to avoid
                    # possible duplicates as the source layers may change.
                    AdministrativeDivision.objects.filter(
                        type__type=division_type, municipality__id=MUNICIPALITY_ID
                    ).delete()

                    for data in dataset:
                        importer.import_districts(data)
            except Exception:
                logger.exception(
                    "Something went wrong while updating division "
                    f"type {division_type}, changes rolled back."
                )

        # Remove stale data for division types that are no longer imported.
        for division_type in OBSOLETE_DIVISION_TYPES:
            logger.info(f"Removing obsolete division type: {division_type}")
            AdministrativeDivision.objects.filter(
                type__type=division_type, municipality__id=MUNICIPALITY_ID
            ).delete()
