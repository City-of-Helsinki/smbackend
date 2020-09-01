import datetime
import pprint

from django.core.management.base import BaseCommand, CommandError
from munigeo.models import AdministrativeDivisionType

from services.models import Unit, UnitAlias

TYPES = [
    "lower_comprehensive_school_district_fi",
    "lower_comprehensive_school_district_sv",
    "upper_comprehensive_school_district_fi",
    "upper_comprehensive_school_district_sv",
]


def get_administrativedivision_types():
    return AdministrativeDivisionType.objects.filter(type__in=TYPES)


def get_division_units():
    results = []
    for adm_type in get_administrativedivision_types():
        for division in adm_type.administrativedivision_set.filter(
            end__gt=datetime.date(year=2017, month=3, day=16)
        ):
            service_point_id = division.service_point_id
            if service_point_id:
                try:
                    unit = Unit.objects.get(id=int(service_point_id))
                except Unit.DoesNotExist:
                    try:
                        unit_alias = UnitAlias.objects.get(second=service_point_id)
                        unit = unit_alias.first
                    except UnitAlias.DoesNotExist:
                        unit = None
                results.append(
                    {
                        "unit": unit,
                        "division": division,
                        "origin_service_point_id": service_point_id,
                        "time": (division.start, division.end),
                        "type": adm_type,
                    }
                )
    return results


def verify_school_units_found():
    division_units = get_division_units()
    missing = {}
    for record in division_units:
        if record["unit"] is None:
            missing.setdefault(record["type"], []).append(record)

    success = True
    error_report = []
    for key, val in missing.items():
        if len(val) > 0:
            success = False
        error_report.append(pprint.pformat(val, indent=4))
    return success, "\n\n".join(error_report)


def verify_school_units_enclosed():
    division_units = get_division_units()
    success = True
    error_report = []
    error_count = 0
    full_count = 0
    for record in division_units:
        unit = record["unit"]
        division = record["division"]
        full_count += 1
        if unit and not division.geometry.boundary.contains(unit.location):
            error_count += 1
            error_report.append(
                {
                    "error": "Geometry not contained within area",
                    "division": division,
                    "start": division.start,
                    "unit": unit,
                    "geom": unit.location.wkt,
                    "unit.srid": unit.location.srid,
                    "div.srid": division.geometry.boundary.srid,
                }
            )
            success = False
    return (
        success,
        (
            "{} errors \n".format(error_count)
            + "\n\n".join([pprint.pformat(error, indent=4) for error in error_report])
        ),
    )


class Command(BaseCommand):
    help = """ Verify that imported school district data correctly refers to
    existing units and is otherwise valid.  """

    def handle(self, *args, **options):
        success, errors = verify_school_units_found()
        if success is False:
            raise CommandError("Missing units " + errors)
        success, errors = verify_school_units_enclosed()
        if success is False:
            raise CommandError("Non-enclosed units " + errors)
