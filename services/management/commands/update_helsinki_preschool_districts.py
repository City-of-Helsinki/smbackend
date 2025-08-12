import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from munigeo.models import AdministrativeDivision

from services.management.commands.school_district_import.school_district_importer import (  # noqa: E501
    SchoolDistrictImporter,
)

logger = logging.getLogger(__name__)

PRESCHOOL_DISTRICT_DATA = [
    {
        "source_type": "avoindata:Esiopetusalue_suomi",
        "division_type": "preschool_education_fi",
        "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
    },
    {
        "source_type": "avoindata:Esiopetusalue_suomi_tuleva",
        "division_type": "preschool_education_fi",
        "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
    },
    {
        "source_type": "avoindata:Esiopetusalue_ruotsi",
        "division_type": "preschool_education_sv",
        "ocd_id": "esiopetuksen_oppilaaksiottoalue_sv",
    },
    {
        "source_type": "avoindata:Esiopetusalue_ruotsi_tuleva",
        "division_type": "preschool_education_sv",
        "ocd_id": "esiopetuksen_oppilaaksiottoalue_sv",
    },
]


class Command(BaseCommand):
    help = (
        "Update Helsinki preschool districts. "
        "Usage: ./manage.py update_helsinki_preschool_districts"
    )

    @transaction.atomic
    def handle(self, *args, **options):
        importer = SchoolDistrictImporter(district_type="preschool")

        data_by_division_type = {}
        for data in PRESCHOOL_DISTRICT_DATA:
            data_by_division_type.setdefault(data["division_type"], []).append(data)

        for division_type in data_by_division_type.keys():
            logger.info(f"Updating division type: {division_type}")
            try:
                with transaction.atomic():
                    # Remove old divisions before importing new ones to avoid possible
                    # duplicates as the source layers may change
                    AdministrativeDivision.objects.filter(
                        type__type=division_type, municipality__id="helsinki"
                    ).delete()

                    for data in data_by_division_type[division_type]:
                        importer.import_districts(data)
            except Exception:
                logger.exception(
                    "Something went wrong while updating division "
                    f"type {division_type}, changes rolled back."
                )

        for division_type in data_by_division_type.keys():
            importer.remove_old_school_year(division_type)
