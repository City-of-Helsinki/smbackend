from datetime import datetime, timezone

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from services.management.commands.services_import.services import update_service_counts
from services.models import Service, ServiceNode, Unit
from services.tests.test_service_node_view_set_api import create_municipality
from services.tests.utils import get

MODIFIED_TIME = datetime(
    year=2023, month=1, day=1, hour=1, minute=1, second=1, tzinfo=timezone.utc
)


def create_services():
    ServiceNode.objects.create(id=100, last_modified_time=MODIFIED_TIME)
    Service.objects.create(
        id=1,
        name="Neuvonta",
        last_modified_time=MODIFIED_TIME,
    )
    Service.objects.create(
        id=2,
        name="Palveluseteli",
        last_modified_time=MODIFIED_TIME,
        root_service_node_id=100,
    )
    Service.objects.create(
        id=3,
        name="Kuntoutus",
        last_modified_time=MODIFIED_TIME,
    )


def create_related_unit(service):
    municipality = create_municipality()
    unit = Unit.objects.create(
        id=17682, municipality=municipality, last_modified_time=MODIFIED_TIME
    )
    service.units.add(unit)
    service.save()
    update_service_counts()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_service_list(api_client):
    create_services()
    response = get(api_client, reverse("service-list"))
    assert response.status_code == 200
    assert response.data["count"] == 3


@pytest.mark.django_db
def test_get_service_fields(api_client):
    create_services()
    service = Service.objects.get(id=2)
    create_related_unit(service)
    response = get(api_client, reverse("service-detail", kwargs={"pk": 2}))
    assert response.status_code == 200
    assert response.data["id"] == 2
    assert response.data["name"]["fi"] == "Palveluseteli"
    assert response.data["root_service_node"] == 100
    assert response.data["period_enabled"] is True  # default value
    assert response.data["clarification_enabled"] is True  # default value
    assert response.data["keywords"] == {}
    assert response.data["unit_count"]["municipality"] == {"helsinki": 1}
    assert response.data["unit_count"]["total"] == 1


@pytest.mark.django_db
def test_id_filter(api_client):
    create_services()
    response = get(api_client, reverse("service-list"), data={"id": "2,3"})
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"][0]["id"] == 3
    assert response.data["results"][1]["id"] == 2
