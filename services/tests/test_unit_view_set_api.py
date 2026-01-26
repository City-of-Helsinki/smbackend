from datetime import datetime

import pytest
import pytz
from django.contrib.gis.geos import GEOSGeometry
from django.urls import reverse
from munigeo import api as munigeo_api
from munigeo.api import DEFAULT_SRS
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)
from rest_framework.test import APIClient

from services.api import make_muni_ocd_id
from services.models import Department, MobilityServiceNode, Service, ServiceNode, Unit
from services.models.unit import PROJECTION_SRID
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
        description_fi="Kuvaus suomeksi",
        description_sv="Beskrivning på svenska",
        description_en="Description in English",
        provider_type=2,
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

    # Unit with "not displayed" service
    Unit.objects.create(
        id=7,
        last_modified_time=datetime.now(UTC_TIMEZONE),
        displayed_service_owner_type="NOT_DISPLAYED",
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


def create_mobility_nodes():
    mobility_node_1 = MobilityServiceNode.objects.create(
        id=1000000, name_fi="Liikenne", last_modified_time=datetime.now(UTC_TIMEZONE)
    )
    mobility_node_2 = MobilityServiceNode.objects.create(
        id=513,
        name_fi="Joukkoliikenne",
        parent_id=1000000,
        last_modified_time=datetime.now(UTC_TIMEZONE),
    )
    mobility_node_3 = MobilityServiceNode.objects.create(
        id=514,
        name_fi="Asiakaspalvelu",
        parent_id=1000000,
        last_modified_time=datetime.now(UTC_TIMEZONE),
    )

    return mobility_node_1, mobility_node_2, mobility_node_3


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
    assert response.data["count"] == 5
    assert results[0]["id"] == 7
    assert results[1]["id"] == 4
    assert results[2]["id"] == 3
    assert results[3]["id"] == 2
    assert results[4]["id"] == 1


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


@pytest.mark.django_db
def test_mobility_node_filter(api_client):
    """
    Test that only units with given mobility service nodes are visible in unit view when given "mobility_node" parameter.
    """
    create_units()
    mobility_node_1, mobility_node_2, mobility_node_3 = create_mobility_nodes()
    unit_1 = Unit.objects.get(id=1)
    unit_2 = Unit.objects.get(id=2)
    unit_1.mobility_service_nodes.add(mobility_node_2)
    unit_1.mobility_service_nodes.add(mobility_node_3)
    unit_2.mobility_service_nodes.add(mobility_node_3)

    # mobility_node_2 and mobility_node_3 are children of mobility_node_1, so querying with mobility_node_1 should
    # return units linked with both mobility_node_2 and mobility_node_3
    response = get(
        api_client, reverse("unit-list"), data={"mobility_node": mobility_node_1.id}
    )
    assert response.status_code == 200
    assert response.data["count"] == 2

    # Querying with both mobility_node_2 and mobility_node_3 should return units linked with either of them
    response = get(
        api_client,
        reverse("unit-list"),
        data={"mobility_node": f"{mobility_node_2.id},{mobility_node_3.id}"},
    )
    assert response.status_code == 200
    assert response.data["count"] == 2

    response = get(
        api_client, reverse("unit-list"), data={"mobility_node": mobility_node_2.id}
    )
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == 1


@pytest.mark.django_db
def test_geometry_3d_parameter(api_client):
    """
    Test that geometry_3d parameter returns 3D geometries.
    """
    create_units()
    wkt = "MULTILINESTRING Z ((1 2 3, 4 5 6, 7 8 9), (10 11 12, 13 14 15, 16 17 18))"
    geometry_3d = GEOSGeometry(wkt, srid=PROJECTION_SRID)
    unit = Unit.objects.get(id=1)
    unit.geometry_3d = geometry_3d
    unit.save()

    # When geometry_3d parameter is not given, 3D geometries are not returned
    response = get(api_client, reverse("unit-list"))
    results = response.data["results"]
    assert response.status_code == 200
    assert "geometry_3d" not in results[0]

    response = get(api_client, reverse("unit-list"), data={"geometry_3d": True})
    results = response.data["results"]
    assert response.status_code == 200
    assert results[4]["id"] == 1
    assert results[4]["geometry_3d"]["type"] == "MultiLineString"
    assert (
        results[4]["geometry_3d"]["coordinates"]
        == munigeo_api.geom_to_json(geometry_3d, DEFAULT_SRS)["coordinates"]
    )


@pytest.mark.django_db
def test_translations(api_client):
    """
    Test that translations are returned correctly.
    """
    create_units()
    response = get(api_client, reverse("unit-list"))
    results = response.data["results"]
    unit_with_translations = results[4]
    assert unit_with_translations["id"] == 1
    assert unit_with_translations["description"]["fi"] == "Kuvaus suomeksi"
    assert unit_with_translations["description"]["sv"] == "Beskrivning på svenska"
    assert unit_with_translations["description"]["en"] == "Description in English"


@pytest.mark.django_db
def test_id_filter(api_client):
    create_units()
    response = get(api_client, reverse("unit-list"), data={"id": "2,3"})
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"][0]["id"] == 3
    assert response.data["results"][1]["id"] == 2


@pytest.mark.django_db
def tests_provider_type_filter(api_client):
    create_units()
    response = get(api_client, reverse("unit-list"), data={"provider_type": 2})
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == 1


@pytest.mark.django_db
def test_provider_type_not_filter(api_client):
    create_units()
    response = get(api_client, reverse("unit-list"), data={"provider_type__not": 2})
    assert response.status_code == 200
    assert response.data["count"] == 4


@pytest.mark.django_db
def test_heightprofilegeom_parameter(api_client):
    create_units()
    wkt = "MULTILINESTRING Z ((1 2 3, 4 5 6, 7 8 9), (10 11 12, 13 14 15, 16 17 18))"
    geometry_3d = GEOSGeometry(wkt, srid=PROJECTION_SRID)
    unit = Unit.objects.get(id=1)
    unit.geometry_3d = geometry_3d
    unit.save()

    # When heightprofilegeom parameter is not given, height_profile_geom is not returned
    response = get(api_client, reverse("unit-list"))
    results = response.data["results"]
    assert response.status_code == 200
    assert "height_profile_geom" not in results

    response = get(api_client, reverse("unit-list"), data={"heightprofilegeom": True})
    results = response.data["results"]
    assert response.status_code == 200
    assert results[4]["id"] == 1
    assert results[4]["height_profile_geom"]["type"] == "FeatureCollection"
    assert (
        results[4]["height_profile_geom"]["features"][0]["geometry"]["type"]
        == "LineString"
    )
    assert (
        results[4]["height_profile_geom"]["features"][0]["geometry"]["coordinates"]
        == munigeo_api.geom_to_json(geometry_3d, DEFAULT_SRS)["coordinates"][0]
    )
    assert (
        results[4]["height_profile_geom"]["features"][0]["properties"]["attributeType"]
        == "flat"
    )
    assert (
        results[4]["height_profile_geom"]["features"][1]["geometry"]["coordinates"]
        == munigeo_api.geom_to_json(geometry_3d, DEFAULT_SRS)["coordinates"][1]
    )
    assert (
        results[4]["height_profile_geom"]["features"][1]["properties"]["attributeType"]
        == "flat"
    )

    assert results[4]["height_profile_geom"]["properties"]["summary"] == "Height"
    assert results[4]["height_profile_geom"]["properties"]["label"] == "Height profile"
    assert (
        results[4]["height_profile_geom"]["properties"]["label_fi"] == "Korkeusprofiili"
    )
    assert results[4]["height_profile_geom"]["properties"]["label_sv"] == "Höjdprofil"


@pytest.mark.django_db
def test_service_filter_returns_distinct_units(api_client):
    """
    Test that units with multiple services are not duplicated in results when filtering by service.
    This tests the fix for distinct("id") in service filtering.
    """
    create_units()

    # Create services
    service_1 = Service.objects.create(
        id=100, name="Service 1", last_modified_time=datetime.now(UTC_TIMEZONE)
    )
    service_2 = Service.objects.create(
        id=101, name="Service 2", last_modified_time=datetime.now(UTC_TIMEZONE)
    )

    # Add multiple services to the same unit
    unit_1 = Unit.objects.get(id=1)
    unit_1.services.add(service_1, service_2)

    # Filter by both services - unit should appear only once
    response = get(
        api_client,
        reverse("unit-list"),
        data={"service": f"{service_1.id},{service_2.id}"},
    )

    assert response.status_code == 200
    # Unit 1 should appear only once, not twice
    assert response.data["count"] == 1
    unit_ids = [result["id"] for result in response.data["results"]]
    assert unit_ids.count(1) == 1
    assert response.data["results"][0]["id"] == 1


@pytest.mark.django_db
def test_service_node_filter_returns_distinct_units(api_client):
    """
    Test that units with multiple service nodes are not duplicated when filtering.
    This tests the fix for distinct("id") in service_node filtering.
    """
    create_units()
    (
        service_node_1,
        service_node_2,
        service_node_3,
        service_node_4,
    ) = create_service_nodes()

    # Add multiple service nodes to the same unit
    unit_1 = Unit.objects.get(id=1)
    unit_1.service_nodes.add(service_node_2, service_node_3)

    # Filter by parent service node that includes both child nodes
    response = get(
        api_client, reverse("unit-list"), data={"service_node": service_node_1.id}
    )

    assert response.status_code == 200
    # Unit 1 should appear only once, despite having multiple matching service nodes
    unit_ids = [result["id"] for result in response.data["results"]]
    assert unit_ids.count(1) == 1

    # Also test with explicit list of both service nodes
    response = get(
        api_client,
        reverse("unit-list"),
        data={"service_node": f"{service_node_2.id},{service_node_3.id}"},
    )

    assert response.status_code == 200
    unit_ids = [result["id"] for result in response.data["results"]]
    # Unit 1 should still appear only once
    assert unit_ids.count(1) == 1


@pytest.mark.django_db
def test_exclude_service_node_filter_returns_distinct_units(api_client):
    """
    Test that units are not duplicated when using exclude_service_nodes filter.
    This tests the fix for distinct("id") in exclude_service_nodes filtering.
    """
    create_units()
    (
        service_node_1,
        service_node_2,
        service_node_3,
        service_node_4,
    ) = create_service_nodes()

    # Create units with service nodes
    unit_1 = Unit.objects.get(id=1)
    unit_2 = Unit.objects.get(id=2)
    unit_3 = Unit.objects.get(id=3)

    # unit_1 has service_node_4 only
    unit_1.service_nodes.add(service_node_4)

    # unit_2 has both service_node_2 and service_node_4
    unit_2.service_nodes.add(service_node_2, service_node_4)

    # unit_3 has service_node_2 only
    unit_3.service_nodes.add(service_node_2)

    # Exclude service_node_2 - should get units without it
    response = get(
        api_client,
        reverse("unit-list"),
        data={"exclude_service_nodes": service_node_2.id},
    )

    assert response.status_code == 200
    unit_ids = [result["id"] for result in response.data["results"]]

    # Each unit should appear only once
    assert len(unit_ids) == len(set(unit_ids)), "Duplicate units found in results"

    # Units with service_node_2 should be excluded
    assert 3 not in unit_ids
    assert 2 not in unit_ids


@pytest.mark.django_db
def test_mobility_node_filter_returns_distinct_units(api_client):
    """
    Test that units with multiple mobility service nodes are not duplicated.
    This tests the fix for distinct("id") in mobility_node filtering.
    """
    create_units()
    mobility_node_1, mobility_node_2, mobility_node_3 = create_mobility_nodes()

    # Add multiple mobility nodes to the same unit
    unit_1 = Unit.objects.get(id=1)
    unit_1.mobility_service_nodes.add(mobility_node_2, mobility_node_3)

    # Filter by parent mobility node that includes both child nodes
    response = get(
        api_client, reverse("unit-list"), data={"mobility_node": mobility_node_1.id}
    )

    assert response.status_code == 200
    unit_ids = [result["id"] for result in response.data["results"]]
    # Unit 1 should appear only once, despite having multiple matching mobility nodes
    assert unit_ids.count(1) == 1

    # Also test with explicit list of both mobility nodes
    response = get(
        api_client,
        reverse("unit-list"),
        data={"mobility_node": f"{mobility_node_2.id},{mobility_node_3.id}"},
    )

    assert response.status_code == 200
    unit_ids = [result["id"] for result in response.data["results"]]
    # Unit 1 should still appear only once
    assert unit_ids.count(1) == 1


@pytest.mark.django_db
def test_category_filter_returns_distinct_units(api_client):
    """
    Test that category filter (combining services and service_nodes) returns distinct units.
    This tests the fix for distinct("id") in category filtering.
    """
    create_units()

    # Create service and service node
    service_1 = Service.objects.create(
        id=100, name="Service 1", last_modified_time=datetime.now(UTC_TIMEZONE)
    )
    service_node_1, _, _, _ = create_service_nodes()

    unit_1 = Unit.objects.get(id=1)
    # Add both service and service_node to the same unit
    unit_1.services.add(service_1)
    unit_1.service_nodes.add(service_node_1)

    # Filter by category including both the service and service_node
    response = get(
        api_client,
        reverse("unit-list"),
        data={"category": f"service:{service_1.id},service_node:{service_node_1.id}"},
    )

    assert response.status_code == 200
    # Unit 1 should appear only once, not twice (once for service, once for service_node)
    assert response.data["count"] == 1
    unit_ids = [result["id"] for result in response.data["results"]]
    assert unit_ids.count(1) == 1
    assert response.data["results"][0]["id"] == 1
