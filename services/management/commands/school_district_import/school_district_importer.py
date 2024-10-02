import logging
import re
from datetime import datetime

from django.contrib.gis.gdal import CoordTransform, DataSource, SpatialReference
from django.contrib.gis.geos import MultiPolygon
from munigeo import ocd
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

from services.management.commands.lipas_import import MiniWFS

logger = logging.getLogger(__name__)
SRID = 3067


class SchoolDistrictImporter:
    WFS_BASE = "https://kartta.hel.fi/ws/geoserver/avoindata/wfs"

    def __init__(self, district_type):
        self.district_type = district_type

    def import_districts(self, data):
        """
        Data is a dictionary containing the following keys:
        - source_type: The name of the WFS layer to fetch
        - division_type:  AdministrativeDivisionType type of the division
        - ocd_id: The key to use in the OCD ID generation

        """
        wfs = MiniWFS(self.WFS_BASE)
        municipality = Municipality.objects.get(id="helsinki")

        source_type = data["source_type"]
        division_type = data["division_type"]
        ocd_id = data["ocd_id"]

        try:
            url = wfs.get_feature(type_name=source_type)
            layer = DataSource(url)[0]
        except Exception as e:
            logger.error(f"Error retrieving data for {source_type}: {e}")
            return

        logger.info(f"Retrieved {len(layer)} {source_type} features.")
        logger.info("Processing data...")

        division_type_obj, _ = AdministrativeDivisionType.objects.get_or_create(
            type=division_type
        )

        for feature in layer:
            self.import_division(
                feature,
                division_type_obj,
                municipality,
                ocd_id,
                source_type,
            )

    def import_division(
        self, feature, division_type_obj, municipality, ocd_id, source_type
    ):
        origin_id = feature.get("id")
        if not origin_id:
            logger.info("Skipping feature without id.")
            return

        division, _ = AdministrativeDivision.objects.get_or_create(
            origin_id=origin_id, type=division_type_obj
        )

        division.municipality = municipality
        division.parent = municipality.division

        division.ocd_id = ocd.make_id(
            **{ocd_id: str(origin_id), "parent": municipality.division.ocd_id}
        )

        service_point_id = str(feature.get("toimipiste_id"))

        if self.district_type == "school":
            division.service_point_id = service_point_id
            division.units = [service_point_id]

            if "suomi" in source_type:
                name = feature.get("nimi_fi")
                division.name_fi = feature.get("nimi_fi")
                division.start = self.create_start_date(name)
                division.end = self.create_end_date(name)
            if "ruotsi" in source_type:
                name = feature.get("nimi_se")
                division.name_sv = feature.get("nimi_se")
                division.start = self.create_start_date(name)
                division.end = self.create_end_date(name)

        elif self.district_type == "preschool":
            units = service_point_id.split(",")
            division.units = units

            division.name_fi = feature.get("nimi_fi")
            division.name_sv = feature.get("nimi_se")

            division.extra = {"schoolyear": feature.get("lukuvuosi")}

        division.save()

        self.save_geometry(feature, division)

    def create_start_date(self, name):
        year = re.split(r"[ -]", name)[-2]
        return f"{year}-08-01"

    def create_end_date(self, name):
        year = re.split(r"[ -]", name)[-1]
        return f"{year }-07-31"

    def save_geometry(self, feature, division):
        geom = feature.geom
        if not geom.srid:
            geom.srid = SRID
        if geom.srid != SRID:
            geom.transform(SRID)
            ct = CoordTransform(SpatialReference(geom.srid), SpatialReference(SRID))
            geom.transform(ct)

        geom = geom.geos
        if geom.geom_type == "Polygon":
            geom = MultiPolygon(geom.buffer(0), srid=geom.srid)

        try:
            geom_obj = division.geometry
        except AdministrativeDivisionGeometry.DoesNotExist:
            geom_obj = AdministrativeDivisionGeometry(division=division)

        geom_obj.boundary = geom
        geom_obj.save()

    def remove_old_school_year(self, division_type):
        """
        During 1.8.-15.12. only the current school year is shown.
        During 16.12.-31.7. both the current and the next school year are shown.

        The source might be named as "tuleva" but it might still actually be the current school year.

        If today is between 1.8.-15.12 delete the previous year.
        """
        division_type_obj = AdministrativeDivisionType.objects.get(type=division_type)

        today = datetime.today()

        last_year = today.year - 1
        last_year_start_date = f"{last_year}-08-01"

        if datetime(today.year, 8, 1) <= today <= datetime(today.year, 12, 15):
            if self.district_type == "school":
                AdministrativeDivision.objects.filter(
                    type=division_type_obj,
                    start=last_year_start_date,
                ).delete()

            if self.district_type == "preschool":
                AdministrativeDivision.objects.filter(
                    type=division_type_obj,
                    extra__schoolyear=f"{last_year}-{last_year + 1}",
                ).delete()
