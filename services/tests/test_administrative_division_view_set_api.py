import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.urls import reverse
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
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


def create_test_area():
    """
    Create a simple test area in Helsinki center.
    """
    polygon_coords = [
        (24.928, 60.178),  # top left
        (24.948, 60.178),  # top right
        (24.948, 60.159),  # bottom right
        (24.928, 60.159),  # bottom left
        (24.928, 60.178),  # Close the ring by repeating the first point
    ]
    polygon = Polygon(polygon_coords, srid=4326)  # WGS84 srid
    multi_polygon = MultiPolygon(polygon, srid=4326)
    multi_polygon.transform(settings.DEFAULT_SRID)
    return multi_polygon


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


@pytest.mark.django_db
def test_address_filter(api_client):
    create_administrative_divisions()
    division = AdministrativeDivision.objects.get(name="helsinki")
    AdministrativeDivisionGeometry.objects.create(
        division=division, boundary=create_test_area()
    )

    response = get(
        api_client,
        reverse("administrativedivision-list"),
        data={
            "municipality": "helsinki",
            "address": "Kaivokatu 1",
        },  # An address in the test area
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["municipality"] == "helsinki"

    response = get(
        api_client,
        reverse("administrativedivision-list"),
        data={
            "municipality": "helsinki",
            "address": "Katajanokanranta 1",
        },  # An address outside the test area
    )

    assert response.status_code == 200
    assert response.data["count"] == 0
