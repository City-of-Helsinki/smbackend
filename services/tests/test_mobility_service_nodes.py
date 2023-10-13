import datetime

import pytest

from services.management.commands.services_import.services import (
    update_mobility_service_nodes,
)
from services.models import MobilityServiceNode, ServiceNode

MODIFIED_TIME = datetime.datetime(
    year=2023, month=1, day=1, hour=1, minute=1, second=1, tzinfo=datetime.timezone.utc
)


@pytest.fixture
def service_nodes():
    ServiceNode.objects.create(
        id=513, name_fi="Joukkoliikenne", last_modified_time=MODIFIED_TIME
    )
    ServiceNode.objects.create(
        id=514,
        name_fi="Asiakaspalvelu",
        parent_id=513,
        last_modified_time=MODIFIED_TIME,
    )
    ServiceNode.objects.create(
        id=515, name_fi="Pysäkit", parent_id=513, last_modified_time=MODIFIED_TIME
    )
    return ServiceNode.objects.all()


@pytest.mark.django_db
def test_update_mobility_service_nodes(service_nodes):
    """
    Test that update_mobility_service_nodes() creates:
        - By default "traffic_node" with id 1000000 and the "mobility_node" with id 1000001 as set in
          MOBILITY_SERVICE_NODE_MAPPING
        - Based on existing ServiceNodes new MobilityServiceNodes with id 513 and 514
        - But it should not create new MobilityServiceNode with id 515 since it is in the
          MOBILITY_SERVICE_NODE_EXCLUDE_NODES list
    """
    assert MobilityServiceNode.objects.count() == 0
    update_mobility_service_nodes()
    assert MobilityServiceNode.objects.count() == 4
    assert MobilityServiceNode.objects.filter(id=1000000).exists()
    assert MobilityServiceNode.objects.filter(id=1000001).exists()
    assert MobilityServiceNode.objects.filter(id=513).exists()
    assert MobilityServiceNode.objects.filter(id=514).exists()
    assert not MobilityServiceNode.objects.filter(id=515).exists()
