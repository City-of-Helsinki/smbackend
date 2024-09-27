import logging
from datetime import datetime

from django.contrib.gis.gdal import CoordTransform, DataSource, SpatialReference
from django.contrib.gis.geos import MultiPolygon
from django.core.management.base import BaseCommand, CommandError
from munigeo import ocd
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

from services.management.commands.lipas_import import MiniWFS

logger = logging.getLogger(__name__)

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

WFS_BASE = "https://kartta.hel.fi/ws/geoserver/avoindata/wfs"
SRID = 3067


class Command(BaseCommand):
    help = (
        "Update Helsinki school districts. "
        "Usage: ./manage.py update_helsinki_school_districts <start_date_current> <end_date_current> "
        "<start_date_future> <end_date_future>"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "start_date_current",
            type=str,
            help="Start date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "end_date_current",
            type=str,
            help="End date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "start_date_future",
            type=str,
            help="Start date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "end_date_future",
            type=str,
            help="End date in YYYY-MM-DD format",
        )

    def handle(self, *args, **options):
        start_date_current, end_date_current, start_date_future, end_date_future = (
            self.parse_dates(options)
        )
        logger.info(f"Retrieving data from {WFS_BASE}...")

        wfs = MiniWFS(WFS_BASE)
        municipality = Municipality.objects.get(id="helsinki")

        for data in SCHOOL_DISTRICT_DATA:
            self.import_districts(
                data,
                wfs,
                municipality,
                start_date_current,
                end_date_current,
                start_date_future,
                end_date_future,
            )

    def parse_dates(self, options):
        try:
            start_date_current = datetime.strptime(
                options["start_date_current"], "%Y-%m-%d"
            )
            end_date_current = datetime.strptime(
                options["end_date_current"], "%Y-%m-%d"
            )
            start_date_future = datetime.strptime(
                options["start_date_future"], "%Y-%m-%d"
            )
            end_date_future = datetime.strptime(options["end_date_future"], "%Y-%m-%d")
            return (
                start_date_current,
                end_date_current,
                start_date_future,
                end_date_future,
            )
        except ValueError:
            raise CommandError("Dates must be in the format YYYY-MM-DD.")

    def import_districts(
        self,
        data,
        wfs,
        municipality,
        start_date_current,
        end_date_current,
        start_date_future,
        end_date_future,
    ):
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

        division_type_obj = AdministrativeDivisionType.objects.get(type=division_type)

        for feature in layer:
            self.update_division(
                feature,
                division_type_obj,
                municipality,
                ocd_id,
                source_type,
                start_date_current,
                end_date_current,
                start_date_future,
                end_date_future,
            )

    def update_division(
        self,
        feature,
        division_type_obj,
        municipality,
        ocd_id,
        source_type,
        start_date_current,
        end_date_current,
        start_date_future,
        end_date_future,
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
        service_point_id = feature.get("toimipiste_id")
        division.service_point_id = service_point_id
        division.units = [service_point_id]
        division.ocd_id = ocd.make_id(
            **{ocd_id: str(origin_id), "parent": municipality.division.ocd_id}
        )

        if "suomi" in source_type:
            division.name_fi = feature.get("nimi_fi")
        if "ruotsi" in source_type:
            division.name_sv = feature.get("nimi_se")

        if "tuleva" in source_type:
            division.start = start_date_future
            division.end = end_date_future
        else:
            division.start = start_date_current
            division.end = end_date_current

        division.save()
        self.save_geometry(feature, division)

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
