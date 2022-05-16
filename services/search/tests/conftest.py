import pytest
from django.contrib.gis.geos import Point
from django.utils.timezone import now
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
    Street,
)
from rest_framework.test import APIClient

from services.management.commands.index_search_columns import get_search_column
from services.models import Service, Unit


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def units(services):
    units = []
    unit = Unit.objects.create(
        id=1,
        name="test unit",
        last_modified_time=now(),
    )
    unit.services.add(1)
    unit.save()
    units.append(unit)
    unit = Unit.objects.create(
        id=2,
        name="Museo",
        name_sv="Museum",
        last_modified_time=now(),
    )
    unit.services.add(2)
    unit.save()
    units.append(unit)
    unit = Unit.objects.create(
        id=3,
        name="Biologinen Museo",
        last_modified_time=now(),
    )
    unit.services.add(2)
    unit.save()
    units.append(unit)
    service = services[2]
    unit = Unit.objects.create(
        id=4,
        name="Impivaara",
        service_names_fi=[service.name_fi],
        last_modified_time=now(),
    )
    unit.services.add(3)
    unit.save()
    units.append(unit)
    Unit.objects.update(search_column_fi=get_search_column(Unit, "fi"))
    return units


@pytest.mark.django_db
@pytest.fixture
def services():
    services = []
    service = Service.objects.create(
        id=1,
        name="test service",
        last_modified_time=now(),
    )
    services.append(service)
    service = Service.objects.create(
        id=2,
        name="Museot",
        name_sv="Museum",
        last_modified_time=now(),
    )
    services.append(service)
    service = Service.objects.create(
        id=3,
        name="Uimahalli",
        name_sv="Simhall",
        last_modified_time=now(),
    )
    services.append(service)
    Service.objects.update(search_column_fi=get_search_column(Service, "fi"))
    return services


@pytest.mark.django_db
@pytest.fixture
def addresses(streets, municipality):
    addresses = []
    location = Point(60.479032, 22.25417, srid=4326)
    addr = Address.objects.create(
        id=1,
        street_id=42,
        location=location,
        full_name="Kurrapolku 1A",
        municipality=municipality,
    )
    addresses.append(addr)
    location = Point(60.379032, 22.15417)
    addr = Address.objects.create(
        id=2,
        street_id=43,
        location=location,
        full_name="Markulantie 2B",
        municipality=municipality,
    )
    addresses.append(addr)
    Address.objects.update(search_column_fi=get_search_column(Address, "fi"))
    return addresses


@pytest.mark.django_db
@pytest.fixture
def municipality():
    muni = Municipality.objects.create(id="helsinki", name="Helsinki")
    return muni


@pytest.mark.django_db
@pytest.fixture
def administrative_division_type():
    adm_div_type = AdministrativeDivisionType.objects.create(
        id=1, type="muni", name="Municipality"
    )
    return adm_div_type


@pytest.mark.django_db
@pytest.fixture
def administrative_division(administrative_division_type):
    adm_div = AdministrativeDivision.objects.get_or_create(
        name="Helsinki", origin_id=91, type_id=1
    )
    AdministrativeDivision.objects.update(
        search_column_fi=get_search_column(AdministrativeDivision, "fi")
    )
    return adm_div


@pytest.mark.django_db
@pytest.fixture
def streets(municipality):
    streets = []
    street = Street.objects.create(id=42, name="Kurrapolku", municipality_id="helsinki")
    streets.append(street)
    street = Street.objects.create(
        id=43, name="Markulantie", municipality_id="helsinki"
    )
    streets.append(street)
    return streets
