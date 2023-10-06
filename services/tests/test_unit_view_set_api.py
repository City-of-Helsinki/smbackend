from datetime import datetime

import pytest
import pytz
from django.urls import reverse
from rest_framework.test import APIClient

from services.models import Unit
from services.tests.utils import get


def create_units():
    utc_timezone = pytz.timezone("UTC")
    # Unit with public service
    Unit.objects.create(
        id=1,
        last_modified_time=datetime.now(utc_timezone),
        displayed_service_owner_type="MUNICIPAL_SERVICE",
    )
    # Unit with private service
    Unit.objects.create(
        id=2,
        last_modified_time=datetime.now(utc_timezone),
        displayed_service_owner_type="PRIVATE_SERVICE",
    )
    # Unit with public enterprise
    Unit.objects.create(
        id=3, last_modified_time=datetime.now(utc_timezone), organizer_type=6
    )
    # Unit with private enterprise
    Unit.objects.create(
        id=4, last_modified_time=datetime.now(utc_timezone), organizer_type=10
    )
    # Non-public unit
    Unit.objects.create(
        id=5, last_modified_time=datetime.now(utc_timezone), public=False
    )

    # Inactive unit
    Unit.objects.create(
        id=6, last_modified_time=datetime.now(utc_timezone), is_active=False
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_unit_list(api_client):
    """
    Test that public and active units are visible in unit view.
    """
    create_units()

    response = get(api_client, reverse("unit-list"))
    results = response.data["results"]

    assert response.status_code == 200
    assert response.data["count"] == 4
    assert results[0]["id"] == 4
    assert results[1]["id"] == 3
    assert results[2]["id"] == 2
    assert results[3]["id"] == 1


@pytest.mark.django_db
def test_no_private_services_filter(api_client):
    """
    Test that private services are not visible in unit view when given "no_private_services" parameter.
    """
    create_units()

    response = get(api_client, reverse("unit-list"), data={"no_private_services": True})
    results = response.data["results"]

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert results[0]["id"] == 3
    assert results[1]["id"] == 1
