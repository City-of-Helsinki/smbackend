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
from pytest_django.asserts import assertNumQueries
from rest_framework.test import APIClient

from services.api import make_muni_ocd_id
from services.models import (
    Department,
    Keyword,
    MobilityServiceNode,
    Service,
    ServiceNode,
    Unit,
    UnitAlias,
    UnitConnection,
)
from services.models.unit import PROJECTION_SRID
from services.tests.utils import get

UTC_TIMEZONE = pytz.timezone("UTC")

# Expected database query counts for unit retrieve operations with proper prefetching.
# These represent the actual query counts after optimization to prevent N+1 issues.
# Before optimization: 64+ queries (N+1 for each related object)
# After optimization: ~12-14 queries (prefetch_related eliminates N+1)
EXPECTED_QUERIES_UNIT_RETRIEVE = 12
EXPECTED_QUERIES_UNIT_RETRIEVE_WITH_ALIAS = 14


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
def test_service_filtering(api_client):
    """
    Test service filtering.
    """
    create_units()

    # Create services and associate them with units
    service1 = Service.objects.create(
        id=695, name="Service 1", last_modified_time=datetime.now(UTC_TIMEZONE)
    )
    service2 = Service.objects.create(
        id=406, name="Service 2", last_modified_time=datetime.now(UTC_TIMEZONE)
    )
    service3 = Service.objects.create(
        id=235, name="Service 3", last_modified_time=datetime.now(UTC_TIMEZONE)
    )

    unit1 = Unit.objects.get(id=1)
    unit2 = Unit.objects.get(id=2)
    unit3 = Unit.objects.get(id=3)

    # Associate units with multiple services to test M2M optimization
    service1.units.add(unit1, unit2)
    service2.units.add(unit2, unit3)
    service3.units.add(unit1)

    # Test single service filtering
    response = get(api_client, reverse("unit-list"), data={"service": "695"})
    assert response.status_code == 200
    assert response.data["count"] == 2
    unit_ids = {result["id"] for result in response.data["results"]}
    assert unit_ids == {1, 2}

    # Test multiple service filtering (this was causing HARAKIRI due to distinct() performance issues)
    response = get(api_client, reverse("unit-list"), data={"service": "695,406,235"})
    assert response.status_code == 200
    assert response.data["count"] == 3
    unit_ids = {result["id"] for result in response.data["results"]}
    assert unit_ids == {1, 2, 3}

    # Test with non-existent service
    response = get(api_client, reverse("unit-list"), data={"service": "999"})
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.django_db
def test_service_node_filtering(api_client):
    """
    Test service node filtering.
    """
    create_units()
    service_node_1, service_node_2, service_node_3, service_node_4 = (
        create_service_nodes()
    )

    unit1 = Unit.objects.get(id=1)
    unit2 = Unit.objects.get(id=2)
    unit3 = Unit.objects.get(id=3)

    # Associate units with service nodes
    unit1.service_nodes.add(service_node_2)
    unit2.service_nodes.add(service_node_2, service_node_3)
    unit3.service_nodes.add(service_node_3, service_node_4)

    # Test multiple service node filtering
    response = get(
        api_client,
        reverse("unit-list"),
        data={
            "service_node": f"{service_node_2.id},{service_node_3.id},{service_node_4.id}"
        },
    )
    assert response.status_code == 200
    assert response.data["count"] == 3
    unit_ids = {result["id"] for result in response.data["results"]}
    assert unit_ids == {1, 2, 3}


@pytest.mark.django_db
def test_exclude_service_nodes_filtering(api_client):
    """
    Test exclude service nodes filtering.
    """
    create_units()
    service_node_1, service_node_2, service_node_3, service_node_4 = (
        create_service_nodes()
    )

    unit1 = Unit.objects.get(id=1)
    unit2 = Unit.objects.get(id=2)
    unit3 = Unit.objects.get(id=3)
    Unit.objects.get(id=4)
    Unit.objects.get(id=7)

    # Associate units with service nodes
    unit1.service_nodes.add(service_node_2)
    unit2.service_nodes.add(service_node_3)
    unit3.service_nodes.add(service_node_4)

    # Test excluding service nodes
    response = get(
        api_client,
        reverse("unit-list"),
        data={"exclude_service_nodes": f"{service_node_2.id},{service_node_3.id}"},
    )
    assert response.status_code == 200
    # Should exclude units 1 and 2, leaving units 3, 4, 7
    assert response.data["count"] == 3
    unit_ids = {result["id"] for result in response.data["results"]}
    assert unit_ids == {3, 4, 7}


@pytest.mark.django_db
def test_mobility_node_filtering(api_client):
    """
    Test mobility node filtering.
    """
    create_units()
    mobility_node_1, mobility_node_2, mobility_node_3 = create_mobility_nodes()

    unit1 = Unit.objects.get(id=1)
    unit2 = Unit.objects.get(id=2)
    unit3 = Unit.objects.get(id=3)

    # Associate units with mobility service nodes
    unit1.mobility_service_nodes.add(mobility_node_2)
    unit2.mobility_service_nodes.add(mobility_node_2, mobility_node_3)
    unit3.mobility_service_nodes.add(mobility_node_3)

    # Test multiple mobility node filtering
    response = get(
        api_client,
        reverse("unit-list"),
        data={"mobility_node": f"{mobility_node_2.id},{mobility_node_3.id}"},
    )
    assert response.status_code == 200
    assert response.data["count"] == 3
    unit_ids = {result["id"] for result in response.data["results"]}
    assert unit_ids == {1, 2, 3}


@pytest.mark.django_db
def test_category_filtering(api_client):
    """
    Test category filtering.
    """
    create_units()
    service_node_1, service_node_2, service_node_3, service_node_4 = (
        create_service_nodes()
    )

    # Create services
    service1 = Service.objects.create(
        id=100, name="Service 100", last_modified_time=datetime.now(UTC_TIMEZONE)
    )
    service2 = Service.objects.create(
        id=200, name="Service 200", last_modified_time=datetime.now(UTC_TIMEZONE)
    )

    unit1 = Unit.objects.get(id=1)
    unit2 = Unit.objects.get(id=2)
    unit3 = Unit.objects.get(id=3)

    # Associate units with services and service nodes
    service1.units.add(unit1)
    service2.units.add(unit2)
    unit3.service_nodes.add(service_node_4)

    # Test category filtering with both services and service nodes
    response = get(
        api_client,
        reverse("unit-list"),
        data={"category": f"service:100,service:200,service_node:{service_node_4.id}"},
    )
    assert response.status_code == 200
    assert response.data["count"] == 3
    unit_ids = {result["id"] for result in response.data["results"]}
    assert unit_ids == {1, 2, 3}


@pytest.mark.django_db
def test_unit_retrieve_prevents_n_plus_1_queries(api_client):
    """
    Test that retrieving a single unit does not cause N+1 queries.

    This test ensures that UnitViewSet.retrieve() uses the optimized
    get_queryset() with prefetch_related to avoid N+1 database queries.
    """
    create_units()
    service_nodes = create_service_nodes()
    unit = Unit.objects.get(id=1)
    unit.service_nodes.add(service_nodes[0], service_nodes[1])
    keyword1 = Keyword.objects.create(name="keyword1")
    keyword2 = Keyword.objects.create(name="keyword2")
    unit.keywords.add(keyword1, keyword2)
    UnitConnection.objects.create(
        unit=unit,
        name="Phone",
        section_type=UnitConnection.PHONE_OR_EMAIL_TYPE,
    )
    UnitConnection.objects.create(
        unit=unit,
        name="Website",
        section_type=UnitConnection.LINK_TYPE,
    )

    with assertNumQueries(EXPECTED_QUERIES_UNIT_RETRIEVE):
        response = get(api_client, reverse("unit-detail", kwargs={"pk": unit.id}))

    assert response.status_code == 200
    assert response.data["id"] == unit.id


@pytest.mark.django_db
def test_unit_retrieve_with_include_parameter(api_client):
    """
    Test that unit retrieve with include parameter still uses prefetching.
    Verifies that the fix works correctly with query parameters.
    """
    create_units()
    service_nodes = create_service_nodes()
    unit = Unit.objects.get(id=1)
    unit.service_nodes.add(service_nodes[0])
    UnitConnection.objects.create(
        unit=unit,
        name="Connection",
        section_type=UnitConnection.PHONE_OR_EMAIL_TYPE,
    )

    with assertNumQueries(EXPECTED_QUERIES_UNIT_RETRIEVE):
        response = get(
            api_client,
            reverse("unit-detail", kwargs={"pk": unit.id}),
            data={"include": "service_nodes,connections"},
        )

    assert response.status_code == 200
    assert "service_nodes" in response.data
    assert "connections" in response.data


@pytest.mark.django_db
def test_unit_retrieve_via_alias_prevents_n_plus_1(api_client):
    """
    Test that retrieving a unit via UnitAlias does not cause N+1 queries.

    Verifies that when a unit is accessed via an alias, the prefetch
    optimizations are still applied and filters (public, is_active) are
    enforced. This prevents the N+1 issue from being reintroduced through
    the alias path.
    """
    create_units()
    service_nodes = create_service_nodes()
    unit = Unit.objects.get(id=1)
    unit.service_nodes.add(service_nodes[0])
    keyword = Keyword.objects.create(name="test_keyword")
    unit.keywords.add(keyword)
    UnitConnection.objects.create(
        unit=unit,
        name="Test Connection",
        section_type=UnitConnection.PHONE_OR_EMAIL_TYPE,
    )
    UnitAlias.objects.create(first=unit, second=9999)

    with assertNumQueries(EXPECTED_QUERIES_UNIT_RETRIEVE_WITH_ALIAS):
        response = get(api_client, reverse("unit-detail", kwargs={"pk": 9999}))

    assert response.status_code == 200
    assert response.data["id"] == unit.id


@pytest.mark.django_db
def test_unit_alias_respects_public_and_active_filters(api_client):
    """
    Test that UnitAlias lookups respect public and is_active filters.

    Ensures that accessing a unit via alias still enforces the queryset
    filters, preventing access to non-public or inactive units.
    """
    create_units()

    non_public_unit = Unit.objects.get(id=5)
    inactive_unit = Unit.objects.get(id=6)
    UnitAlias.objects.create(first=non_public_unit, second=8888)
    UnitAlias.objects.create(first=inactive_unit, second=7777)

    response = api_client.get(reverse("unit-detail", kwargs={"pk": 8888}))
    assert response.status_code == 404

    response = api_client.get(reverse("unit-detail", kwargs={"pk": 7777}))
    assert response.status_code == 404
