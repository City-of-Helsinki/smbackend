from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.urls import reverse
from django.utils import timezone
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)
from rest_framework.test import APIClient

from services.api import make_muni_ocd_id
from services.models import Unit
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
def municipality():
    """
    Fixture to create a sample municipality for testing.
    """
    return Municipality.objects.create(id="helsinki", name="Helsinki")


@pytest.fixture
def administrative_division_type():
    """
    Fixture to create a sample administrative division type for testing.
    """
    return AdministrativeDivisionType.objects.create(type="muni")


@pytest.fixture
def administrative_division(administrative_division_type, municipality):
    """
    Fixture to create a sample administrative division for testing.
    """
    return AdministrativeDivision.objects.create(
        type=administrative_division_type,
        name="Test Division",
        ocd_id="ocd-division/test-muni/test-division",
        municipality=municipality,
    )


@pytest.fixture
def unit():
    """
    Fixture to create a sample unit associated with an administrative division.
    """
    unit = Unit.objects.create(
        id=123,
        name="Test Unit",
        location=Point(60.1709, 24.9375, srid=4326),  # Helsinki center
        public=True,
        is_active=True,
        last_modified_time=timezone.now(),
    )

    return unit


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
def test_get_administrative_division_detail(api_client, administrative_division):
    response = get(
        api_client,
        reverse("administrativedivision-detail", args=[administrative_division.id]),
    )

    assert response.status_code == 200
    assert response.data["name"]["fi"] == "Test Division"
    assert response.data["ocd_id"] == "ocd-division/test-muni/test-division"


@pytest.mark.django_db
def test_get_units_in_division(api_client, administrative_division, unit):
    administrative_division.units = [unit.id]
    administrative_division.save()

    response = get(
        api_client,
        reverse("administrativedivision-detail", args=[administrative_division.id]),
        data={"unit_include": "name"},
    )

    assert response.status_code == 200
    assert "units" in response.data
    assert len(response.data["units"]) == 1
    assert response.data["units"][0]["name"]["fi"] == "Test Unit"


@pytest.mark.django_db
def test_units_is_empty_if_no_units_found(api_client, administrative_division, unit):
    administrative_division.units = [98765]  # Non-existent unit ID
    administrative_division.save()

    response = get(
        api_client,
        reverse("administrativedivision-detail", args=[administrative_division.id]),
        data={"unit_include": "name"},
    )

    assert response.status_code == 200
    assert "units" in response.data
    assert response.data["units"] == []


@pytest.mark.django_db
def test_get_unit_in_division(api_client, administrative_division, unit):
    administrative_division.service_point_id = str(unit.id)
    administrative_division.save()

    response = get(
        api_client,
        reverse("administrativedivision-detail", args=[administrative_division.id]),
        data={"unit_include": "name"},
    )

    assert response.status_code == 200
    assert response.data["service_point_id"] == str(unit.id)
    assert "unit" in response.data
    assert response.data["unit"]["name"]["fi"] == "Test Unit"


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
@patch("services.api.geocode_address")
def test_address_filter(mock_geocode_address, api_client):
    create_administrative_divisions()
    division = AdministrativeDivision.objects.get(name="helsinki")
    AdministrativeDivisionGeometry.objects.create(
        division=division, boundary=create_test_area()
    )

    # Mock geocode_address to return coordinates inside the test area
    # Test area is approximately: lat 60.159-60.178, lon 24.928-24.948
    mock_geocode_address.return_value = (60.168, 24.938)  # Inside the test area

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

    # Mock geocode_address to return coordinates outside the test area
    mock_geocode_address.return_value = (60.150, 24.920)  # Outside the test area

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


@pytest.mark.django_db
def test_translations(api_client):
    """
    Test that the translations are returned correctly.
    """
    create_administrative_divisions()
    division = AdministrativeDivision.objects.get(name="helsinki")
    division.name_fi = "Eteläinen"
    division.name_sv = "Södra"
    division.save()

    response = get(
        api_client,
        reverse("administrativedivision-list"),
        data={"municipality": "helsinki"},
    )

    assert response.data["results"][0]["name"]["fi"] == "Eteläinen"
    assert response.data["results"][0]["name"]["sv"] == "Södra"
