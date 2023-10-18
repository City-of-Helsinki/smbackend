from datetime import datetime

import pytest
import pytz
from django.urls import reverse
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)
from rest_framework.test import APIClient

from services.api import make_muni_ocd_id
from services.models import Department, ServiceNode, Unit
from services.tests.utils import get

UTC_TIMEZONE = pytz.timezone("UTC")


def create_units():
    municipality_id = "helsinki"
    division_type = AdministrativeDivisionType.objects.create(type="muni")
    division = AdministrativeDivision.objects.create(
        type=division_type,
        name=municipality_id,
        ocd_id=make_muni_ocd_id(municipality_id),
    )
    municipality = Municipality.objects.create(
        id=municipality_id, name=municipality_id, division=division
    )
    organization = Department.objects.create(
        name_fi="Helsingin kaupunki",
        municipality=municipality,
        uuid="83e74666-0836-4c1d-948a-4b34a8b90301",
    )
    department = Department.objects.create(
        name_fi="Stara",
        uuid="a10eb4e7-c7e3-49ec-b6cd-54a1cb74adf8",
    )
    # Unit with public service
    Unit.objects.create(
        id=1,
        last_modified_time=datetime.now(UTC_TIMEZONE),
        displayed_service_owner_type="MUNICIPAL_SERVICE",
        root_department=organization,
        municipality=municipality,
    )
    # Unit with private service
    Unit.objects.create(
        id=2,
        last_modified_time=datetime.now(UTC_TIMEZONE),
        displayed_service_owner_type="PRIVATE_SERVICE",
        root_department=organization,
        department=department,
    )
    # Unit with public enterprise
    Unit.objects.create(
        id=3,
        last_modified_time=datetime.now(UTC_TIMEZONE),
        organizer_type=6,
        municipality=municipality,
    )
    # Unit with private enterprise
    Unit.objects.create(
        id=4,
        last_modified_time=datetime.now(UTC_TIMEZONE),
        organizer_type=10,
        department=department,
    )

    # Non-public unit
    Unit.objects.create(
        id=5, last_modified_time=datetime.now(UTC_TIMEZONE), public=False
    )

    # Inactive unit
    Unit.objects.create(
        id=6, last_modified_time=datetime.now(UTC_TIMEZONE), is_active=False
    )


def create_service_nodes():
    service_node_1 = ServiceNode.objects.create(
        id=513, name_fi="Joukkoliikenne", last_modified_time=datetime.now(UTC_TIMEZONE)
    )
    service_node_2 = ServiceNode.objects.create(
        id=514,
        name_fi="Asiakaspalvelu",
        parent_id=513,
        last_modified_time=datetime.now(UTC_TIMEZONE),
    )
    service_node_3 = ServiceNode.objects.create(
        id=515,
        name_fi="Pysäkit",
        parent_id=513,
        last_modified_time=datetime.now(UTC_TIMEZONE),
    )
    service_node_4 = ServiceNode.objects.create(
        id=600,
        name_fi="Kirjastot",
        last_modified_time=datetime.now(UTC_TIMEZONE),
    )
    return service_node_1, service_node_2, service_node_3, service_node_4


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


@pytest.mark.django_db
def test_organizations_filter(api_client):
    """
    Test that organization's units are visible in unit view when "organization" parameter is given.
    """
    create_units()

    response = get(
        api_client,
        reverse("unit-list"),
        data={"organization": "83e74666-0836-4c1d-948a-4b34a8b90301"},
    )
    results = response.data["results"]

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert results[0]["id"] == 2
    assert results[1]["id"] == 1


@pytest.mark.django_db
def test_organizations_filter_with_department(api_client):
    """
    Test that department's units are visible in unit view when "organization" parameter is given.
    """
    create_units()

    response = get(
        api_client,
        reverse("unit-list"),
        data={"organization": "a10eb4e7-c7e3-49ec-b6cd-54a1cb74adf8"},
    )
    results = response.data["results"]

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert results[0]["id"] == 4
    assert results[1]["id"] == 2


@pytest.mark.django_db
def test_organizations_filter_with_multiple_departments(api_client):
    """
    Test that department's units are visible in unit view when multiple "organization" parameters are given.
    """
    create_units()

    response = get(
        api_client,
        reverse("unit-list"),
        data={
            "organization": "83e74666-0836-4c1d-948a-4b34a8b90301,a10eb4e7-c7e3-49ec-b6cd-54a1cb74adf8"
        },
    )
    results = response.data["results"]

    assert response.status_code == 200
    assert response.data["count"] == 3
    assert results[0]["id"] == 4
    assert results[1]["id"] == 2
    assert results[2]["id"] == 1


@pytest.mark.django_db
def test_municipality_filter(api_client):
    """
    Test that municipality's units are visible in unit view when "municipality" parameter is given.
    """
    create_units()

    response = get(
        api_client,
        reverse("unit-list"),
        data={"municipality": "helsinki"},
    )
    results = response.data["results"]

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert results[0]["id"] == 3
    assert results[1]["id"] == 1


@pytest.mark.django_db
def test_service_node_filter(api_client):
    """
    Test that only units with given service nodes are visible in unit view when given "service_node" parameter.
    """
    create_units()
    (
        service_node_1,
        service_node_2,
        service_node_3,
        service_node_4,
    ) = create_service_nodes()
    unit_1 = Unit.objects.get(id=1)
    unit_2 = Unit.objects.get(id=2)
    unit_3 = Unit.objects.get(id=3)
    unit_1.service_nodes.add(service_node_2)
    unit_2.service_nodes.add(service_node_2)
    unit_2.service_nodes.add(service_node_3)
    unit_3.service_nodes.add(service_node_3)
    unit_3.service_nodes.add(service_node_4)

    # service_node_2 and service_node_3 are children of service_node_1, so querying with service_node_1 should return
    # units linked with service_node_2 and service_node_3
    response = get(
        api_client, reverse("unit-list"), data={"service_node": service_node_1.id}
    )
    results = response.data["results"]
    assert response.status_code == 200
    assert response.data["count"] == 3
    assert results[0]["id"] == 3
    assert results[1]["id"] == 2
    assert results[2]["id"] == 1

    # Querying with both service_node_3 and service_node_4 should return units linked with either of them
    response = get(
        api_client,
        reverse("unit-list"),
        data={"service_node": f"{service_node_3.id},{service_node_4.id}"},
    )
    results = response.data["results"]
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert results[0]["id"] == 3
    assert results[1]["id"] == 2

    # Querying with service_node_4 should return units linked only with service_node_4
    response = get(
        api_client, reverse("unit-list"), data={"service_node": service_node_4.id}
    )
    results = response.data["results"]
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert results[0]["id"] == 3
