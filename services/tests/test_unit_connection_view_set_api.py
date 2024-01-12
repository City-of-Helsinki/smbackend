from datetime import datetime

import pytest
import pytz
from django.urls import reverse
from rest_framework.test import APIClient

from services.models import Unit, UnitConnection
from services.tests.utils import get


def create_unit_connections():
    unit = Unit.objects.create(id=1, last_modified_time=datetime.now(pytz.utc))
    UnitConnection.objects.create(
        id=100,
        unit=unit,
        name="ma-pe 9.00-17.00",
        section_type=UnitConnection.OPENING_HOURS_TYPE,
        www="https://test",
        email="test@test",
        phone="1234567890",
        contact_person="Test Person",
        tags=["#aukioloajat"],
    )
    UnitConnection.objects.create(
        unit=unit, name="Info", section_type=UnitConnection.OTHER_INFO_TYPE
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_unit_connection_list(api_client):
    create_unit_connections()
    response = get(api_client, reverse("unitconnection-list"))

    assert response.status_code == 200
    assert response.data["count"] == 2


@pytest.mark.django_db
def test_get_unit_connection_detail(api_client):
    create_unit_connections()
    response = get(api_client, reverse("unitconnection-detail", kwargs={"pk": 100}))

    assert response.status_code == 200
    assert response.data["id"] == 100
    assert response.data["unit"] == 1
    assert response.data["name"]["fi"] == "ma-pe 9.00-17.00"
    assert response.data["section_type"] == "OPENING_HOURS"
    assert response.data["www"]["fi"] == "https://test"
    assert response.data["email"] == "test@test"
    assert response.data["phone"] == "1234567890"
    assert response.data["contact_person"] == "Test Person"
    assert response.data["tags"] == ["#aukioloajat"]
