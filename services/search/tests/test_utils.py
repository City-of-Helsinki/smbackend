import logging

import pytest
from django.utils.timezone import now
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)

from services.models import ServiceNode, Unit
from services.search.utils import set_service_node_unit_count


@pytest.fixture
def municipality(db):
    AdministrativeDivisionType.objects.get_or_create(
        id=1, type="muni", name="Municipality"
    )
    AdministrativeDivision.objects.get_or_create(
        id=1, name="Helsinki", origin_id=853, type_id=1
    )
    return Municipality.objects.create(
        division_id=1, id="helsinki", name="Helsinki", name_sv="Helsingfors"
    )


@pytest.fixture
def service_node_with_unit(municipality):
    node = ServiceNode.objects.create(
        id=10,
        name="Test Node",
        last_modified_time=now(),
    )
    unit = Unit.objects.create(
        id=100,
        name="Test Unit",
        last_modified_time=now(),
        municipality=municipality,
        public=True,
        is_active=True,
    )
    unit.service_nodes.add(node)
    unit.save()
    return node


@pytest.fixture
def second_service_node_with_unit(municipality):
    node = ServiceNode.objects.create(
        id=11,
        name="Second Test Node",
        last_modified_time=now(),
    )
    unit = Unit.objects.create(
        id=101,
        name="Second Test Unit",
        last_modified_time=now(),
        municipality=municipality,
        public=True,
        is_active=True,
    )
    unit.service_nodes.add(node)
    unit.save()
    return node


@pytest.mark.django_db
def test_set_service_node_unit_count_skips_missing_service_node(
    service_node_with_unit,
):
    valid_id = str(service_node_with_unit.id)
    missing_id = "9999"

    representation = {}
    set_service_node_unit_count([valid_id, missing_id], representation)

    assert "unit_count" in representation
    assert "municipality" in representation["unit_count"]
    assert representation["unit_count"]["municipality"].get("helsinki", 0) >= 1
    assert representation["unit_count"]["total"] >= 1


@pytest.mark.django_db
def test_set_service_node_unit_count_skips_missing_logs_warning(
    service_node_with_unit, caplog
):
    valid_id = str(service_node_with_unit.id)
    missing_id = "9999"

    representation = {}
    with caplog.at_level(logging.WARNING, logger="search"):
        set_service_node_unit_count([valid_id, missing_id], representation)

    warning_messages = [
        r.message for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert len(warning_messages) == 1
    assert missing_id in warning_messages[0]


@pytest.mark.django_db
def test_set_service_node_unit_count_all_ids_missing(caplog):
    missing_ids = ["8888", "9999"]

    representation = {}
    with caplog.at_level(logging.WARNING, logger="search"):
        set_service_node_unit_count(missing_ids, representation)

    assert representation["unit_count"]["total"] == 0
    assert representation["unit_count"]["municipality"] == {}

    warning_messages = [
        r.message for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert len(warning_messages) == len(missing_ids)
    for missing_id in missing_ids:
        assert any(missing_id in msg for msg in warning_messages)


@pytest.mark.django_db
def test_set_service_node_unit_count_only_valid_grouped_ids(
    service_node_with_unit, second_service_node_with_unit
):
    ids = [str(service_node_with_unit.id), str(second_service_node_with_unit.id)]

    representation = {}
    set_service_node_unit_count(ids, representation)

    assert representation["unit_count"]["total"] >= 2
    assert representation["unit_count"]["municipality"].get("helsinki", 0) >= 2
