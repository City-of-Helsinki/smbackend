from datetime import datetime, timezone

import pytest
from django.urls import reverse
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)
from rest_framework.test import APIClient

from services.api import make_muni_ocd_id
from services.management.commands.services_import.services import (
    update_service_node_counts,
)
from services.models import Service, ServiceNode, Unit
from services.tests.utils import get

MODIFIED_TIME = datetime(
    year=2023, month=1, day=1, hour=1, minute=1, second=1, tzinfo=timezone.utc
)


def create_service_nodes():
    ServiceNode.objects.create(
        id=1400, name="Asuminen", last_modified_time=MODIFIED_TIME
    )
    ServiceNode.objects.create(
        id=8, name="Vuokra-asuminen", parent_id=1400, last_modified_time=MODIFIED_TIME
    )
    ServiceNode.objects.create(
        id=11, name="Opiskelija-asunnot", parent_id=8, last_modified_time=MODIFIED_TIME
    )


def create_related_service(service_node):
    service = Service.objects.create(
        id=1, name="Opiskelija-asunnot", last_modified_time=MODIFIED_TIME
    )
    service_node.related_services.add(service)
    service_node.save()


def create_related_unit(service_node):
    municipality = create_municipality()
    unit = Unit.objects.create(
        id=17682, municipality=municipality, last_modified_time=MODIFIED_TIME
    )
    unit.service_nodes.add(service_node)
    unit.save()
    update_service_node_counts()


def create_municipality():
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
    return municipality


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_service_node_list(api_client):
    create_service_nodes()
    response = get(api_client, reverse("servicenode-list"))
    assert response.status_code == 200
    assert response.data["count"] == 3


@pytest.mark.django_db
def test_level_filter(api_client):
    create_service_nodes()
    response = get(api_client, reverse("servicenode-list"), {"level": 0})
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == 1400


@pytest.mark.django_db
def test_parent_filter(api_client):
    create_service_nodes()
    response = get(api_client, reverse("servicenode-list"), {"parent": 1400})
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == 8


@pytest.mark.django_db
def test_service_node_fields(api_client):
    """
    Test that the fields of a service node are returned correctly
    """
    create_service_nodes()
    service_node = ServiceNode.objects.get(id=8)
    create_related_service(service_node)
    create_related_unit(service_node)

    response = get(api_client, reverse("servicenode-detail", kwargs={"pk": 8}))

    assert response.data["id"] == 8
    assert response.data["children"] == [11]
    assert response.data["name"]["fi"] == "Vuokra-asuminen"
    assert (
        datetime.fromisoformat(response.data["last_modified_time"]).astimezone(
            timezone.utc
        )
        == MODIFIED_TIME
    )
    assert response.data["level"] == 1
    assert response.data["parent"] == 1400
    assert response.data["keywords"] == {}
    assert response.data["related_services"] == [1]
    assert response.data["root"] == 1400
    assert response.data["unit_count"]["municipality"] == {"helsinki": 1}
    assert response.data["unit_count"]["total"] == 1
