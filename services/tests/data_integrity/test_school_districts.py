from munigeo.models import AdministrativeDivisionType
from services.models import Unit, UnitAlias
import pytest
import pprint
import datetime

@pytest.fixture(scope='session')
def django_db_setup():
    """Avoid creating/setting up the test database"""
    pass

@pytest.fixture
def db_access_without_rollback_and_truncate(request, django_db_setup, django_db_blocker):
    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)

TYPES = [
    'lower_comprehensive_school_district_fi',
    'lower_comprehensive_school_district_sv',
    'upper_comprehensive_school_district_fi',
    'upper_comprehensive_school_district_sv',
]

@pytest.mark.django_db
@pytest.fixture
def administrativedivision_types():
    return [AdministrativeDivisionType.objects.get(type=t) for t in TYPES]

@pytest.mark.django_db
@pytest.fixture
def division_units(administrativedivision_types):
    results = []
    for adm_type in administrativedivision_types:
        for division in adm_type.administrativedivision_set.filter(end__gt=datetime.date(year=2017, month=3, day=16)):
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
                results.append({
                    'unit': unit,
                    'division': division,
                    'time': (division.start, division.end),
                    'type': adm_type})
    return results


data_integrity = pytest.mark.skipif(
    not pytest.config.getoption("--data-integrity"),
    reason="need --data-integrity option to run")


@data_integrity
@pytest.mark.django_db
def test__verify_school_units_found(division_units):
    missing = {}
    for record in division_units:
        if record['unit'] is None:
            missing.setdefault(record['type'], []).append(record)

    success = True
    error_report = []
    for key, val in missing.items():
        if len(val) > 0:
            success = False
        error_report.append(pprint.pformat(val, indent=4))
    assert success, "\n\n".join(error_report)


@data_integrity
@pytest.mark.django_db
def test__verify_school_units_enclosed(division_units):
    success = True
    error_report = []
    error_count = 0
    full_count = 0
    for record in division_units:
        unit = record['unit']
        division = record['division']
        full_count += 1
        if unit and not division.geometry.boundary.contains(unit.location):
            error_count += 1
            error_report.append({'error': 'Geometry not contained within area', 'division': division, 'start': division.start, 'unit': unit, 'geom': unit.location.wkt, 'unit.srid': unit.location.srid, 'div.srid': division.geometry.boundary.srid})
            success = False
    assert success, ("{} errors \n".format(error_count) + "\n\n".join([pprint.pformat(error, indent=4) for error in error_report]))
