import pytest
from django.urls import reverse
from munigeo.models import AdministrativeDivision, AdministrativeDivisionType
from rest_framework.test import APIClient

from services.api import make_muni_ocd_id
from services.tests.utils import get


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_administrative_division_list(api_client):
    municipality_id = "helsinki"
    division_type = AdministrativeDivisionType.objects.create(type="muni")
    AdministrativeDivision.objects.create(
        type=division_type,
        name=municipality_id,
        ocd_id=make_muni_ocd_id(municipality_id),
    )

    response = get(api_client, reverse("administrativedivision-list"))
    assert response.status_code == 200
    assert response.data["count"] == 1
