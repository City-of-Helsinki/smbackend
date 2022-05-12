import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
    Street,
)
from rest_framework.test import APIClient

from ..models import ContentType, GroupType, MobileUnit, MobileUnitGroup


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def content_type():
    content_type = ContentType.objects.create(
        type_name="TTT", name="test", description="test content type"
    )
    return content_type


@pytest.mark.django_db
@pytest.fixture
def group_type():
    group_type = GroupType.objects.create(
        type_name="TGT", name="test group", description="test group type"
    )
    return group_type


@pytest.mark.django_db
@pytest.fixture
def mobile_unit(content_type):
    mobile_unit = MobileUnit.objects.create(
        name="Test mobileunit",
        description="Test description",
        content_type=content_type,
        geometry=Point(42.42, 21.21, srid=settings.DEFAULT_SRID),
        extra={"test": "4242"},
    )
    return mobile_unit


@pytest.mark.django_db
@pytest.fixture
def mobile_unit_group(group_type):
    mobile_unit_group = MobileUnitGroup.objects.create(
        name="Test mobileunitgroup",
        description="Test description",
        group_type=group_type,
    )
    return mobile_unit_group


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
    poly = Polygon(
        (
            (1, 1),
            (1, 7000000),
            (7000000, 7000000),
            (7100000, 7100000),
            (7000000, 1),
            (1, 1),
        ),
        srid=3067,
    )
    multi_poly = MultiPolygon(poly, srid=3067)
    adm_div_geom = AdministrativeDivisionGeometry.objects.create(
        id=1, division_id=1, boundary=multi_poly
    )
    return adm_div_geom


@pytest.mark.django_db
@pytest.fixture
def streets():
    streets = []
    street = Street.objects.create(
        name="Test Street",
        name_fi="Test Street",
        name_sv="Test StreetSV",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Linnanpuisto",
        name_fi="Linnanpuisto",
        name_sv="Slottsparken",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Kristiinankatu",
        name_fi="Kristiinankatu",
        name_sv="Kristinegatan",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Pitkäpellonkatu",
        name_fi="Pitkäpellonkatu",
        name_sv="Långåkersgatan",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Kupittaankatu",
        name_fi="Kupittaankatu",
        name_sv="Kuppisgatan",
        municipality_id="turku",
    )
    streets.append(street)
    return streets


@pytest.mark.django_db
@pytest.fixture
def address(streets):
    addresses = []
    location = Point(22.244, 60.4, srid=4326)
    address = Address.objects.create(
        id=100,
        location=location,
        street=streets[0],
        number=42,
        full_name_fi="Test Street 42",
        full_name_sv="Test StreetSV 42",
    )
    addresses.append(address)
    location = Point(22.2265, 60.43504, srid=4326)
    address = Address.objects.create(
        id=101,
        location=location,
        street=streets[1],
        full_name_fi="Linnanpuisto",
        full_name_sv="Slottsparken",
    )
    addresses.append(address)
    location = Point(22.264457, 60.448905, srid=4326)
    address = Address.objects.create(
        id=102,
        location=location,
        street=streets[2],
        number=4,
        full_name_fi="Kristiinankatu 4",
        full_name_sv="Kristinegata 4",
    )
    addresses.append(address)
    location = Point(22.2383, 60.411726, srid=4326)
    address = Address.objects.create(
        id=103,
        location=location,
        street=streets[3],
        number=7,
        full_name_fi="Pitkäpellonkatu 7",
        full_name_sv="Långåkersgatan 7",
    )
    addresses.append(address)
    location = Point(22.2871092678621, 60.44677715747775, srid=4326)
    address = Address.objects.create(
        id=104,
        location=location,
        street=streets[4],
        number=8,
        full_name_fi="Kupittaankatu 8",
        full_name_sv="Kuppisgatan 8",
    )
    addresses.append(address)
    return addresses
