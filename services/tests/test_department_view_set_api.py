import uuid

import pytest
from django.urls import reverse
from munigeo.models import Municipality
from rest_framework.test import APIClient

from services.models import Department
from services.tests.utils import get


def create_departments():
    parent_department = Department.objects.create(
        uuid=uuid.uuid4(),
        name="Test Department Oy",
        organization_type="PRIVATE_ENTERPRISE",
    )
    Department.objects.create(
        uuid=uuid.uuid4(),
        name="Test Department ry",
        parent=parent_department,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_get_department_list(api_client):
    create_departments()
    response = get(api_client, reverse("department-list"))

    assert response.status_code == 200
    assert response.data["count"] == 2


@pytest.mark.django_db
def test_department_fields(api_client):
    """
    Test that fields are returned correctly
    """
    municipality = Municipality.objects.create(id="helsinki", name="Helsinki")
    department = Department.objects.create(
        uuid=uuid.uuid4(),
        business_id="1234567-8",
        name_fi="Testi osasto",
        name_sv="Testavdelning",
        name_en="Test Department",
        abbr="Test",
        street_address="Kaivoskatu 1",
        address_city="Helsinki",
        address_postal_full="00100 Helsinki",
        www="https://hel.fi",
        phone="+358 123 456 789",
        address_zip="00100",
        oid="1234-ABC",
        organization_type="MUNICIPALITY",
        municipality=municipality,
    )

    response = get(
        api_client, reverse("department-detail", kwargs={"pk": department.uuid})
    )

    assert response.status_code == 200
    assert response.data["id"] == department.uuid
    assert response.data["parent"] is None
    assert response.data["business_id"] == department.business_id
    assert response.data["name"]["fi"] == department.name_fi
    assert response.data["name"]["sv"] == department.name_sv
    assert response.data["name"]["en"] == department.name_en
    assert response.data["abbr"]["fi"] == department.abbr
    assert response.data["street_address"]["fi"] == department.street_address
    assert response.data["address_city"]["fi"] == department.address_city
    assert response.data["address_postal_full"]["fi"] == department.address_postal_full
    assert response.data["www"]["fi"] == department.www
    assert response.data["phone"] == department.phone
    assert response.data["address_zip"] == department.address_zip
    assert response.data["oid"] == department.oid
    assert response.data["organization_type"] == department.organization_type
    assert response.data["municipality"] == municipality.id
    assert response.data["level"] == 0


@pytest.mark.django_db
def test_organization_type_filter(api_client):
    """
    Test that organization_type filter return only departments with given organization_type
    """
    create_departments()
    response = get(
        api_client,
        reverse("department-list"),
        data={"organization_type": "PRIVATE_ENTERPRISE"},
    )
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["organization_type"] == "PRIVATE_ENTERPRISE"

    response = get(
        api_client,
        reverse("department-list"),
        data={"organization_type": "OTHER"},
    )
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.django_db
def test_level_filter(api_client):
    """
    Test that level filter return only departments with given level
    """
    create_departments()

    response = get(
        api_client,
        reverse("department-list"),
        data={"level": 0},
    )
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["level"] == 0
    assert response.data["results"][0]["name"]["fi"] == "Test Department Oy"

    response = get(
        api_client,
        reverse("department-list"),
        data={"level": 1},
    )
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["level"] == 1
    assert response.data["results"][0]["name"]["fi"] == "Test Department ry"

    response = get(
        api_client,
        reverse("department-list"),
        data={"level": 2},
    )
    assert response.status_code == 200
    assert response.data["count"] == 0
