import logging
import xml.etree.ElementTree as Et
from functools import lru_cache

from django.contrib.gis.geos import Point, Polygon

from environment_data.constants import REQUEST_SESSION
from environment_data.models import Day, Hour, Month, MonthData, Week, Year, YearData
from mobility_data.importers.constants import (
    SOUTHWEST_FINLAND_BOUNDARY,
    SOUTHWEST_FINLAND_BOUNDARY_SRID,
)

from .constants import NAMESPACES, SOURCE_DATA_SRID, STATION_URL

logger = logging.getLogger(__name__)


def get_stations(match_strings: list):
    response = REQUEST_SESSION.get(STATION_URL)
    stations = []

    if response.status_code == 200:
        polygon = Polygon(
            SOUTHWEST_FINLAND_BOUNDARY, srid=SOUTHWEST_FINLAND_BOUNDARY_SRID
        )
        root = Et.fromstring(response.content)
        monitoring_facilities = root.findall(
            ".//ef:EnvironmentalMonitoringFacility", NAMESPACES
        )
        for mf in monitoring_facilities:
            belongs_to = mf.find("ef:belongsTo", NAMESPACES)
            title = belongs_to.attrib["{http://www.w3.org/1999/xlink}title"]
            if title in match_strings:
                station = {}
                positions = mf.find(".//gml:pos", NAMESPACES).text.split(" ")
                location = Point(
                    float(positions[1]), float(positions[0]), srid=SOURCE_DATA_SRID
                )
                if polygon.covers(location):
                    station["name"] = mf.find("gml:name", NAMESPACES).text
                    station["location"] = location
                    station["geoId"] = mf.find("gml:identifier", NAMESPACES).text
                    stations.append(station)
    else:
        logger.error(
            f"Could not get stations from {STATION_URL}, {response.status_code} {response.content}"
        )

    logger.info(f"Fetched {len(stations)} stations in Southwest Finland.")
    return stations


@lru_cache(maxsize=4069)
def get_or_create_row_cached(model, filter: tuple):
    filter = {key: value for key, value in filter}
    results = model.objects.filter(**filter)
    if results.exists():
        return results.first(), False
    else:
        return model.objects.create(**filter), True


@lru_cache(maxsize=4096)
def get_or_create_hour_row_cached(day, hour_number):
    results = Hour.objects.filter(day=day, hour_number=hour_number)
    if results.exists():
        return results.first(), False
    else:
        return (
            Hour.objects.create(day=day, hour_number=hour_number),
            True,
        )


def create_row(model, filter):
    results = model.objects.filter(**filter)
    if not results.exists():
        model.objects.create(**filter)


def get_or_create_row(model, filter):
    results = model.objects.filter(**filter)
    if results.exists():
        return results.first(), False
    else:
        return model.objects.create(**filter), True


@lru_cache(maxsize=4096)
def get_or_create_day_row_cached(date, year, month, week):
    results = Day.objects.filter(
        date=date,
        weekday_number=date.weekday(),
        year=year,
        month=month,
        week=week,
    )
    if results.exists():
        return results.first(), False
    else:
        return (
            Day.objects.create(
                date=date,
                weekday_number=date.weekday(),
                year=year,
                month=month,
                week=week,
            ),
            True,
        )


@lru_cache(maxsize=4096)
# Use tuple as it is immutable and is hashable for lru_cache
def get_row_cached(model, filter: tuple):
    filter = {key: value for key, value in filter}
    results = model.objects.filter(**filter)
    if results.exists():
        return results.first()
    else:
        return None


@lru_cache(maxsize=64)
def get_year_cached(year_number):
    qs = Year.objects.filter(year_number=year_number)
    if qs.exists():
        return qs.first()
    else:
        return None


@lru_cache(maxsize=128)
def get_year_data_cached(station, year):
    qs = YearData.objects.filter(station=station, year=year)
    if qs.exists():
        return qs.first()
    else:
        return None


@lru_cache(maxsize=256)
def get_month_cached(year, month_number):
    qs = Month.objects.filter(year=year, month_number=month_number)
    if qs.exists():
        return qs.first()
    else:
        return None


@lru_cache(maxsize=256)
def get_month_data_cached(station, month):
    qs = MonthData.objects.filter(station=station, month=month)
    if qs.exists():
        return qs.first()
    else:
        return None


@lru_cache(maxsize=1024)
def get_week_cached(years, week_number):
    qs = Week.objects.filter(years=years, week_number=week_number)
    if qs.exists():
        return qs.first()
    else:
        return None


@lru_cache(maxsize=2048)
def get_day_cached(date):
    qs = Day.objects.filter(date=date)
    if qs.exists():
        return qs.first()
    else:
        return None
