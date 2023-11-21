from datetime import datetime

import pytest
import pytz
from django.urls import reverse
from rest_framework.test import APIClient

from services.models import MobilityServiceNode
from services.tests.utils import get


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_mobility_list(api_client):
    MobilityServiceNode.objects.create(
        id=1, name="Urheilukeskus", last_modified_time=datetime.now(pytz.utc)
    )
    MobilityServiceNode.objects.create(
        id=2,
        name="Kenttä",
        last_modified_time=datetime.now(pytz.utc),
        service_reference="1+2",
    )  # Test that non-integer values in `service_reference` don't break the endpoint

    response = get(api_client, reverse("mobilityservicenode-list"))

    assert response.status_code == 200
    assert response.data["count"] == 2


@pytest.mark.django_db
def test_translations(api_client):
    """
    Test that translations are returned correctly.
    """
    MobilityServiceNode.objects.create(
        id=1,
        name="Frisbeegolf-rata",
        name_sv="Frisbeegolfbana",
        last_modified_time=datetime.now(pytz.utc),
    )
    response = get(api_client, reverse("mobilityservicenode-list"))
    assert response.data["results"][0]["name"]["fi"] == "Frisbeegolf-rata"
    assert response.data["results"][0]["name"]["sv"] == "Frisbeegolfbana"
