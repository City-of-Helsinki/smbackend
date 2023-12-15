from datetime import datetime, timezone

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from services.models import Unit, UnitEntrance
from services.tests.utils import get, get_test_location

MODIFIED_TIME = datetime(
    year=2023, month=1, day=1, hour=1, minute=1, second=1, tzinfo=timezone.utc
)


def create_unit_entrances():
    location = get_test_location(24.852, 60.218, 4326)
    unit = Unit.objects.create(id=23, last_modified_time=MODIFIED_TIME)
    UnitEntrance.objects.create(
        id=1,
        unit=unit,
        is_main_entrance=True,
        name="Test Entrance",
        location=location,
        picture_url="https://test.jpg",
        streetview_url="https://teststreet",
        created_time=MODIFIED_TIME,
        last_modified_time=MODIFIED_TIME,
    )
    UnitEntrance.objects.create(
        id=2,
        unit=unit,
        last_modified_time=MODIFIED_TIME,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_unit_entrance_list(api_client):
    create_unit_entrances()
    response = get(api_client, reverse("unitentrance-list"))
    assert response.status_code == 200
    assert response.data["count"] == 2


@pytest.mark.django_db
def test_get_unit_entrance_fields(api_client):
    create_unit_entrances()

    response = get(api_client, reverse("unitentrance-detail", kwargs={"pk": 1}))

    assert response.status_code == 200
    assert response.data["id"] == 1
    assert response.data["unit"] == 23
    assert response.data["is_main_entrance"] is True
    assert response.data["name"]["fi"] == "Test Entrance"
    assert response.data["location"] == {
        "type": "Point",
        "coordinates": [24.852, 60.218],
    }
    assert response.data["picture_url"] == "https://test.jpg"
    assert response.data["streetview_url"] == "https://teststreet"
    assert (
        datetime.fromisoformat(response.data["last_modified_time"]).astimezone(
            timezone.utc
        )
        == MODIFIED_TIME
    )
    assert (
        datetime.fromisoformat(response.data["last_modified_time"]).astimezone(
            timezone.utc
        )
        == MODIFIED_TIME
    )
