import pytest
from django.urls import reverse
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)
from rest_framework.test import APIClient

from services.api import make_muni_ocd_id
from services.tests.utils import get


def create_administrative_divisions():
    municipality_ids = ["helsinki", "espoo", "vantaa"]
    division_type = AdministrativeDivisionType.objects.create(type="muni")
    for municipality_id in municipality_ids:
        municipality = Municipality.objects.create(
            id=municipality_id, name=municipality_id
        )
        AdministrativeDivision.objects.create(
            type=division_type,
            name=municipality_id,
            ocd_id=make_muni_ocd_id(municipality_id),
            municipality=municipality,
        )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_administrative_division_list(api_client):
    create_administrative_divisions()
    response = get(api_client, reverse("administrativedivision-list"))
    assert response.status_code == 200
    assert response.data["count"] == 3


@pytest.mark.django_db
def test_municipality_filter(api_client):
    create_administrative_divisions()
    response = get(
        api_client,
        reverse("administrativedivision-list"),
        data={"municipality": "helsinki"},
    )
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["municipality"] == "helsinki"
