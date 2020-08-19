import logging
import pytest
from unittest.mock import patch

from services.management.commands.services_import.keyword import KeywordHandler
from services.management.commands.services_import.services import (
    update_service_root_service_nodes,
)
from services.models import Service, ServiceNode
from smbackend_turku.tests.utils import get_test_resource


@pytest.mark.django_db
@patch("smbackend_turku.importers.utils.get_turku_resource")
def test_turku_services_import(get_turku_resource_mock):
    from smbackend_turku.importers.services import ServiceImporter

    logger = logging.getLogger(__name__)
    importer = ServiceImporter(logger=logger)
    keyword_handler = KeywordHandler(logger=importer.logger)

    get_turku_resource_mock.return_value = get_test_resource(resource_name="palvelut")
    importer._import_services(keyword_handler)

    get_turku_resource_mock.return_value = get_test_resource(
        resource_name="palveluluokat"
    )
    importer._import_service_nodes(keyword_handler)

    update_service_root_service_nodes()

    service_1 = Service.objects.get(id=11)
    service_2 = Service.objects.get(id=12)
    node = ServiceNode.objects.get(id=828322097)
    node_parent = ServiceNode.objects.get(id=828322096)

    assert Service.objects.count() == 2
    assert service_1.name == "Tontit"
    assert service_1.name_sv == "Tomter"
    assert service_1.period_enabled is False
    assert service_1.clarification_enabled is False
    assert service_1.root_service_node == node_parent
    assert service_2.name == "Pysäköinti"

    assert ServiceNode.objects.count() == 2
    assert node.name == "Asuminen"
    assert node_parent.name == "Ympäristö"
    assert node_parent.name_sv == "Miljö"
    assert node_parent.name_en == "Environment"

    assert node.parent == node_parent
    assert node in node_parent.children.all()

    assert node.related_services.count() == 1
    assert node_parent.related_services.count() == 2
    assert service_1 in node.related_services.all()
    assert service_2 not in node.related_services.all()
    assert service_1 and service_2 in node_parent.related_services.all()
