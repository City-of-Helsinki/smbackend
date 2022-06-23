import pytest
from django.contrib.gis.geos import GEOSGeometry, Point
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
    PostalCodeArea,
    Street,
)

from mobility_data.tests.conftest import TURKU_WKT


@pytest.mark.django_db
@pytest.fixture
def municipality():
    muni = Municipality.objects.create(id="turku", name="Turku")
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
        id=1, name="Turku", origin_id=853, type_id=1
    )
    return adm_div


@pytest.mark.django_db
@pytest.fixture
def administrative_division_geometry(administrative_division):
    turku_multipoly = GEOSGeometry(TURKU_WKT, srid=3067)
    adm_div_geom = AdministrativeDivisionGeometry.objects.create(
        id=1, division_id=1, boundary=turku_multipoly
    )
    return adm_div_geom


@pytest.mark.django_db
@pytest.fixture
def streets():
    streets = []
    street = Street.objects.create(
        name="Yliopistonkatu",
        name_fi="Yliopistonkatu",
        name_sv="Universitetsgatan",
        municipality_id="turku",
    )
    streets.append(street)
    return streets


@pytest.mark.django_db
@pytest.fixture
def postal_code_areas():
    postal_code_areas = []
    postal_code_area = PostalCodeArea.objects.create(
        postal_code="20100", name="Turku Keskus", name_sv="Åbo Centrum"
    )
    postal_code_areas.append(postal_code_area)
    return postal_code_areas


@pytest.mark.django_db
@pytest.fixture
def address(streets, postal_code_areas, municipality):
    addresses = []
    location = Point(22.26097246971352, 60.45055294118857, srid=4326)
    address = Address.objects.create(
        municipality_id=municipality.id,
        id=105,
        postal_code_area_id=postal_code_areas[0].id,
        location=location,
        street=streets[0],
        number=29,
        full_name_fi="Yliopistonkatu 29",
        full_name_sv="Universitetsgatan 29",
    )
    addresses.append(address)
    return addresses
