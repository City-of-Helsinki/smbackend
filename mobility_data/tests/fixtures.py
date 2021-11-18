import pytest
from rest_framework.test import APIClient
from django.conf import settings
from django.contrib.gis.geos import Point
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