import datetime

import pytest
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from services.management.commands.services_import.services import (
    update_service_node_counts,
)
from services.models import ServiceNode, Unit

from .utils import get

MOD_TIME = datetime.datetime(
    year=2019, month=1, day=1, hour=1, minute=1, second=1, tzinfo=datetime.timezone.utc
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def municipalities():
    t, created = AdministrativeDivisionType.objects.get_or_create(
        id=1, type="muni", defaults={"name": "Municipality"}
    )
    for i, muni_name in enumerate(["a", "b"]):
        a, created = AdministrativeDivision.objects.get_or_create(
            type=t, id=i, name_fi=muni_name
        )
        Municipality.objects.get_or_create(id=muni_name, name_fi=muni_name, division=a)
    return Municipality.objects.all().order_by("pk")


@pytest.fixture
def service_nodes():
    ServiceNode.objects.get_or_create(
        id=1, name_fi="ServiceNode 1", last_modified_time=MOD_TIME
    )
    ServiceNode.objects.get_or_create(
        id=2, name_fi="ServiceNode 2", last_modified_time=MOD_TIME
    )
    ServiceNode.objects.get_or_create(
        id=3, name_fi="ServiceNode 3", last_modified_time=MOD_TIME
    )
    return ServiceNode.objects.all().order_by("pk")


@pytest.fixture
def units(service_nodes, municipalities):
    # |----+----+----+---+----+----|
    # |    | u1 | u2 | u3| u4 | u5 |
    # |----+----+----+---+----+----|
    # | s1 | a  | b  |   |    |    |
    # | s2 | a  |    | - |    |    |
    # | s3 |    |    |   |    | a  |
    # |----+----+----+---+----+----|
    # u     = unit
    # s     = service_node
    # a,b,- = municipality

    a, b = municipalities

    u1, _ = Unit.objects.get_or_create(
        id=1, name_fi="a", municipality=a, last_modified_time=MOD_TIME
    )
    u2, _ = Unit.objects.get_or_create(
        id=2, name_fi="b", municipality=b, last_modified_time=MOD_TIME
    )
    u3, _ = Unit.objects.get_or_create(
        id=3, name_fi="c", municipality=None, last_modified_time=MOD_TIME
    )
    u4, _ = Unit.objects.get_or_create(
        id=4, name_fi="d", municipality=a, last_modified_time=MOD_TIME
    )
    u5, _ = Unit.objects.get_or_create(
        id=5, name_fi="e", municipality=a, last_modified_time=MOD_TIME
    )

    s1, s2, s3 = service_nodes

    u1.service_nodes.add(s1)
    u1.service_nodes.add(s2)
    u2.service_nodes.add(s1)
    u3.service_nodes.add(s2)
    u5.service_nodes.add(s3)

    return Unit.objects.all().order_by("pk")


def get_nodes(api_client):
    response = get(api_client, reverse("servicenode-list"))
    return response.data["results"]


@pytest.mark.django_db
def test_service_node_counts_delete_units(units, api_client):
    for service_node in get_nodes(api_client):
        assert service_node["unit_count"]["total"] == 0
        assert len(service_node["unit_count"]["municipality"]) == 0

    update_service_node_counts()

    def check_before_deletions():
        service_nodes = sorted(get_nodes(api_client), key=lambda x: x["id"])

        service_node_1 = service_nodes[0]
        service_node_2 = service_nodes[1]
        service_node_3 = service_nodes[2]

        assert service_node_1["id"] == 1
        assert service_node_2["id"] == 2
        assert service_node_1["unit_count"]["total"] == 2
        assert service_node_1["unit_count"]["municipality"]["a"] == 1
        assert service_node_1["unit_count"]["municipality"]["b"] == 1
        assert len(service_node_1["unit_count"]["municipality"]) == 2
        assert service_node_2["unit_count"]["total"] == 2
        assert service_node_2["unit_count"]["municipality"]["a"] == 1
        assert service_node_2["unit_count"]["municipality"]["_unknown"] == 1
        assert len(service_node_2["unit_count"]["municipality"]) == 2
        assert service_node_3["unit_count"]["total"] == 1
        assert service_node_3["unit_count"]["municipality"]["a"] == 1
        assert len(service_node_3["unit_count"]["municipality"]) == 1

    check_before_deletions()

    u = Unit.objects.get(pk=4)
    assert u.service_nodes.count() == 0
    u.delete()

    # Deleting a Unit without services shouldn't affect the results
    check_before_deletions()

    # From service nodes 1 & 2 remove one unit with muni 'a' (delete unit)
    Unit.objects.get(pk=1).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x["id"])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]

    assert service_node_1["id"] == 1
    assert service_node_2["id"] == 2
    assert service_node_1["unit_count"]["total"] == 1
    assert service_node_1["unit_count"]["municipality"].get("a") is None
    assert service_node_1["unit_count"]["municipality"]["b"] == 1
    assert len(service_node_1["unit_count"]["municipality"]) == 1
    assert service_node_2["unit_count"]["total"] == 1
    assert service_node_2["unit_count"]["municipality"].get("a") is None
    assert service_node_2["unit_count"]["municipality"]["_unknown"] == 1
    assert len(service_node_2["unit_count"]["municipality"]) == 1
    assert service_node_3["unit_count"]["total"] == 1
    assert service_node_3["unit_count"]["municipality"]["a"] == 1
    assert len(service_node_3["unit_count"]["municipality"]) == 1

    # From service node 3 remove all units (delete unit)
    Unit.objects.get(pk=5).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x["id"])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]

    assert service_node_1["id"] == 1
    assert service_node_2["id"] == 2
    assert service_node_1["unit_count"]["total"] == 1
    assert service_node_1["unit_count"]["municipality"].get("a") is None
    assert service_node_1["unit_count"]["municipality"]["b"] == 1
    assert len(service_node_1["unit_count"]["municipality"]) == 1
    assert service_node_2["unit_count"]["total"] == 1
    assert service_node_2["unit_count"]["municipality"].get("a") is None
    assert service_node_2["unit_count"]["municipality"]["_unknown"] == 1
    assert len(service_node_2["unit_count"]["municipality"]) == 1
    assert service_node_3["unit_count"]["total"] == 0
    assert len(service_node_3["unit_count"]["municipality"]) == 0

    # From service node 2 remove unit with muncipality None
    Unit.objects.get(pk=3).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x["id"])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]

    assert service_node_1["id"] == 1
    assert service_node_2["id"] == 2
    assert service_node_1["unit_count"]["total"] == 1
    assert service_node_1["unit_count"]["municipality"].get("a") is None
    assert service_node_1["unit_count"]["municipality"]["b"] == 1
    assert len(service_node_1["unit_count"]["municipality"]) == 1
    assert service_node_2["unit_count"]["total"] == 0
    assert service_node_2["unit_count"]["municipality"].get("a") is None
    assert service_node_2["unit_count"]["municipality"].get("_unknown") is None
    assert len(service_node_2["unit_count"]["municipality"]) == 0
    assert service_node_3["unit_count"]["total"] == 0
    assert len(service_node_3["unit_count"]["municipality"]) == 0


@pytest.mark.django_db
def test_service_node_counts_add_service_node_to_units(units, api_client):
    # Add service node 3 to all units
    sn3_obj = ServiceNode.objects.get(pk=3)
    for o in Unit.objects.all():
        o.service_nodes.add(sn3_obj)

    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x["id"])
    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]

    assert service_node_1["id"] == 1
    assert service_node_2["id"] == 2
    assert service_node_1["unit_count"]["total"] == 2
    assert service_node_1["unit_count"]["municipality"]["a"] == 1
    assert service_node_1["unit_count"]["municipality"]["b"] == 1
    assert len(service_node_1["unit_count"]["municipality"]) == 2
    assert service_node_2["unit_count"]["total"] == 2
    assert service_node_2["unit_count"]["municipality"]["a"] == 1
    assert service_node_2["unit_count"]["municipality"]["_unknown"] == 1
    assert len(service_node_2["unit_count"]["municipality"]) == 2
    assert service_node_3["unit_count"]["total"] == 5
    assert service_node_3["unit_count"]["municipality"]["a"] == 3
    assert service_node_3["unit_count"]["municipality"]["b"] == 1
    assert service_node_3["unit_count"]["municipality"]["_unknown"] == 1
    assert len(service_node_3["unit_count"]["municipality"]) == 3


@pytest.mark.django_db
def test_service_node_counts_remove_service_node_from_units(units, api_client):
    # Remove service node 1 from all units
    sn1_obj = ServiceNode.objects.get(pk=1)
    for unit in sn1_obj.units.all():
        unit.service_nodes.remove(sn1_obj)

    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x["id"])
    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]

    assert service_node_1["id"] == 1
    assert service_node_2["id"] == 2
    assert service_node_1["unit_count"]["total"] == 0
    assert len(service_node_1["unit_count"]["municipality"]) == 0
    assert service_node_2["unit_count"]["total"] == 2
    assert service_node_2["unit_count"]["municipality"]["a"] == 1
    assert service_node_2["unit_count"]["municipality"]["_unknown"] == 1
    assert len(service_node_2["unit_count"]["municipality"]) == 2
    assert service_node_3["unit_count"]["total"] == 1
    assert service_node_3["unit_count"]["municipality"]["a"] == 1
    assert len(service_node_3["unit_count"]["municipality"]) == 1
