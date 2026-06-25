import logging
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

import requests
from django.db import transaction
from munigeo import ocd
from munigeo.models import AdministrativeDivision, AdministrativeDivisionType

from services.management.commands.school_district_import.base_school_district_importer import (  # noqa: E501
    BaseSchoolDistrictImporter,
)

logger = logging.getLogger(__name__)

LEGACY_EPSG_3879_SRS_NAME = b"http://www.opengis.net/gml/srs/epsg.xml#3879"
EPSG_3879_SRS_NAME = b"EPSG:3879"
ESPOO_WFS_HOST = "kartat.espoo.fi"


class EspooSchoolDistrictImporter(BaseSchoolDistrictImporter):
    """
    Imports Espoo comprehensive school districts.

    The Espoo WFS source only has a single layer per language, but the database
    needs both the current and the next school year populated from it. For each
    feature a division is therefore created for both school years, the OCD ID
    being suffixed with the school year's starting year (e.g. "_2026") to keep
    it unique.
    """

    WFS_BASE = "https://kartat.espoo.fi/teklaogcweb/wfs.ashx"
    MUNICIPALITY_ID = "espoo"

    def prepare_datasource_input(self, url):
        if not url.startswith("WFS:"):
            return url, None

        feature_url = url.removeprefix("WFS:")
        parsed_url = urlparse(feature_url)
        if parsed_url.scheme != "https" or parsed_url.hostname != ESPOO_WFS_HOST:
            raise ValueError(f"Unexpected Espoo WFS URL: {feature_url}")

        response = requests.get(feature_url, timeout=60)
        response.raise_for_status()

        tmpdir = TemporaryDirectory(
            prefix="espoo-school-districts-",
        )
        path = Path(tmpdir.name) / "features.gml"
        path.write_bytes(
            response.content.replace(LEGACY_EPSG_3879_SRS_NAME, EPSG_3879_SRS_NAME)
        )

        return str(path), tmpdir

    def import_districts(self, data):
        """
        Data is a dictionary containing the following keys:
        - source_type: The name of the WFS layer to fetch
        - division_type: AdministrativeDivisionType type of the division
        - ocd_id: The key to use in the OCD ID generation

        """
        municipality = self.get_municipality()

        source_type = data["source_type"]
        division_type = data["division_type"]
        ocd_id = data["ocd_id"]

        layer = self.fetch_layer(source_type)

        division_type_obj, _ = AdministrativeDivisionType.objects.get_or_create(
            type=division_type
        )

        finished_with_errors = False
        for feature in layer:
            for start_year in self.get_school_year_start_years():
                try:
                    with transaction.atomic():
                        self.import_division(
                            feature,
                            division_type_obj,
                            municipality,
                            ocd_id,
                            division_type,
                            start_year,
                        )
                except Exception:
                    logger.exception("Failed to import division, skipping...")
                    finished_with_errors = True

        if finished_with_errors:
            logger.warning(
                "Finished importing districts with errors. See logs for more details."
            )
            raise RuntimeError("Failed to import one or more Espoo school districts.")
        else:
            logger.info("Finished importing districts.")

    def import_division(
        self,
        feature,
        division_type_obj,
        municipality,
        ocd_id,
        division_type,
        start_year,
    ):
        origin_id = feature.get("Id")
        if not origin_id:
            logger.info("Skipping feature without id.")
            return

        # The same source feature is used for both school years, so the year is
        # appended to keep the origin id and OCD id unique per school year.
        suffixed_id = f"{origin_id}_{start_year}"

        division, _ = AdministrativeDivision.objects.get_or_create(
            origin_id=suffixed_id, type=division_type_obj
        )

        division.municipality = municipality
        division.parent = municipality.division

        division.ocd_id = ocd.make_id(
            **{ocd_id: suffixed_id, "parent": municipality.division.ocd_id}
        )

        division.units = []

        name = feature.get("Nimi")
        if division_type.endswith("_sv"):
            division.name_sv = name
        else:
            division.name = name
            division.name_fi = name

        division.start = self.get_start_date(start_year)
        division.end = self.get_end_date(start_year)

        division.save()

        self.save_geometry(feature, division)

    @staticmethod
    def get_school_year_start_years():
        """
        Return the starting years of the current and the next school year.

        A school year starts on 1.8. The current school year therefore started
        this year if today is on or after 1.8., otherwise it started last year.
        """
        today = datetime.today()
        current_start_year = today.year if today.month >= 8 else today.year - 1
        return [current_start_year, current_start_year + 1]

    @staticmethod
    def get_start_date(start_year):
        return f"{start_year}-08-01"

    @staticmethod
    def get_end_date(start_year):
        return f"{start_year + 1}-07-31"
