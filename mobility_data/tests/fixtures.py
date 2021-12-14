import pytest
from rest_framework.test import APIClient
from django.conf import settings
from django.contrib.gis.geos import Point
from munigeo.models import (
    Municipality,
    Address,
    Street,
    AdministrativeDivision,
    AdministrativeDivisionType,
)
from ..models import (
    MobileUnitGroup,
    MobileUnit,
    ContentType,
    GroupType,   
)


@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
@pytest.fixture
def content_type():
    content_type = ContentType.objects.create(
        type_name="TTT",
        name="test",
        description="test content type"
    )
    return content_type

@pytest.mark.django_db
@pytest.fixture
def group_type():
    group_type = GroupType.objects.create(
        type_name="TGT",
        name="test group",
        description="test group type"
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
        extra={"test":"4242"}
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
        id=1,
        type="muni", 
        name="Municipality"
    )
    return adm_div_type

@pytest.mark.django_db
@pytest.fixture
def administrative_division(administrative_division_type):
    adm_div = AdministrativeDivision.objects.get_or_create(
        name="Turku",    
        origin_id=853, 
        type_id=1
    )
    return adm_div
  
@pytest.mark.django_db
@pytest.fixture
def streets():
    streets = []
    street = Street.objects.create(        
        name="Test Street",
        name_fi="Test Street",
        name_sv="Test StreetSV",
        municipality_id="turku"
    )
    streets.append(street)   
    street = Street.objects.create(       
        name="Linnanpuisto",
        name_fi="Linnanpuisto",
        name_sv="LinnanpuistoSV",
        municipality_id="turku"
    )
    streets.append(street) 
    street = Street.objects.create(       
        name="Kristiinankatu",
        name_fi="Kristiinankatu",
        name_sv="Kristinegatan",
        municipality_id="turku"
    )
    streets.append(street) 
    return streets

@pytest.mark.django_db
@pytest.fixture
def address(streets):
    location = Point(22.244, 60.444, srid=3877)
    address = Address.objects.create(
        id=100,
        location=location, 
        street=streets[0], 
        number=42
    ) 
    location = Point(22.241, 60.333, srid=3877)
    address = Address.objects.create(
        id=101,
        location=location, 
        street=streets[1], 
        number=24
    )  
    location = Point(22.241, 60.333, srid=3877)
    address = Address.objects.create(
        id=102,
        location=location, 
        street=streets[2], 
        number=24
    )  
    return address

