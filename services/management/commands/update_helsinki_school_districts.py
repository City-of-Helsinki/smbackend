from django.core.management.base import BaseCommand
from munigeo.models import AdministrativeDivision

from services.management.commands.school_district_import.school_district_importer import (  # noqa: E501
    SchoolDistrictImporter,
)

SCHOOL_DISTRICT_DATA = [
    {
        "source_type": "avoindata:Opev_ooa_alaaste_suomi",
        "division_type": "lower_comprehensive_school_district_fi",
        "ocd_id": "oppilaaksiottoalue_alakoulu",
    },
    {
        "source_type": "avoindata:Opev_ooa_alaaste_suomi_tuleva",
        "division_type": "lower_comprehensive_school_district_fi",
        "ocd_id": "oppilaaksiottoalue_alakoulu",
    },
    {
        "source_type": "avoindata:Opev_ooa_alaaste_ruotsi",
        "division_type": "lower_comprehensive_school_district_sv",
        "ocd_id": "oppilaaksiottoalue_alakoulu_sv",
    },
    {
        "source_type": "avoindata:Opev_ooa_alaaste_ruotsi_tuleva",
        "division_type": "lower_comprehensive_school_district_sv",
        "ocd_id": "oppilaaksiottoalue_alakoulu_sv",
    },
    {
        "source_type": "avoindata:Opev_ooa_ylaaste_suomi",
        "division_type": "upper_comprehensive_school_district_fi",
        "ocd_id": "oppilaaksiottoalue_ylakoulu",
    },
    {
        "source_type": "avoindata:Opev_ooa_ylaaste_suomi_tuleva",
        "division_type": "upper_comprehensive_school_district_fi",
        "ocd_id": "oppilaaksiottoalue_ylakoulu",
    },
    {
        "source_type": "avoindata:Opev_ooa_ylaaste_ruotsi",
        "division_type": "upper_comprehensive_school_district_sv",
        "ocd_id": "oppilaaksiottoalue_ylakoulu_sv",
    },
    {
        "source_type": "avoindata:Opev_ooa_ylaaste_ruotsi_tuleva",
        "division_type": "upper_comprehensive_school_district_sv",
        "ocd_id": "oppilaaksiottoalue_ylakoulu_sv",
    },
]


class Command(BaseCommand):
    help = (
        "Update Helsinki school districts. "
        "Usage: ./manage.py update_helsinki_school_districts"
    )

    def handle(self, *args, **options):
        division_types = list({data["division_type"] for data in SCHOOL_DISTRICT_DATA})

        # Remove old divisions before importing new ones to avoid possible duplicates
        # as the source layers may change
        AdministrativeDivision.objects.filter(
            type__type__in=division_types, municipality__id="helsinki"
        ).delete()

        importer = SchoolDistrictImporter(district_type="school")

        for data in SCHOOL_DISTRICT_DATA:
            importer.import_districts(data)

        for division_type in division_types:
            importer.remove_old_school_year(division_type)
