from django.core.management.base import BaseCommand
from munigeo.models import AdministrativeDivision

from services.management.commands.school_district_import.school_district_importer import (  # noqa: E501
    SchoolDistrictImporter,
)

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

    def handle(self, *args, **options):
        division_types = list(
            {data["division_type"] for data in PRESCHOOL_DISTRICT_DATA}
        )

        # Remove old divisions before importing new ones to avoid possible duplicates
        # as the source layers may change
        AdministrativeDivision.objects.filter(
            type__type__in=division_types, municipality__id="helsinki"
        ).delete()

        importer = SchoolDistrictImporter(district_type="preschool")

        for data in PRESCHOOL_DISTRICT_DATA:
            importer.import_districts(data)

        for division_type in division_types:
            importer.remove_old_school_year(division_type)
