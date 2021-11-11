import logging
from datetime import datetime
from unittest.mock import patch
import pytest
import pytz
from django.conf import settings
from services.models import Service, ServiceNode, Unit
from smbackend_turku.tests.utils import (
    create_municipality,  
    get_test_resource,
)
from smbackend_turku.importers.stations import import_charging_stations
from smbackend_turku.importers.stations import ChargingStationImporter as Importer

@pytest.mark.django_db
def test_charging_stations_import():
    logger = logging.getLogger(__name__)
    utc_timezone = pytz.timezone("UTC")
    # create root servicenode to which the imported service_node will connect
    root_service_node = ServiceNode.objects.create(
        id=42, 
        name="TestRoot", 
        last_modified_time=datetime.now(utc_timezone)
        )
    # Municipality must be created in order to update_service_node_count() 
    # to execute without errors 
    create_municipality()
    #Import using fixture data
    import_charging_stations(
        logger=logger, 
        root_service_node_name="TestRoot",
        test_data=get_test_resource(resource_name="charging_stations")
        )
    service = Service.objects.get(name=Importer.SERVICE_NAME)
    assert service
    assert service.id == settings.CHARGING_STATIONS_IDS["service"]
    service_node = ServiceNode.objects.get(name=Importer.SERVICE_NODE_NAME)
    assert service_node
    assert service_node.id == settings.CHARGING_STATIONS_IDS["service_node"]
    assert service_node.parent.id == root_service_node.id
    
    assert Unit.objects.all().count() == 2
    # second element thus descending order by id.
    assert Unit.objects.all()[1].id == settings.CHARGING_STATIONS_IDS["units_offset"]
    assert Unit.objects.get(name="Hotel Kakola")
    unit = Unit.objects.get(name="AimoPark Stockmann Turku")
    assert unit  
    point = unit.location
    # Tranform to source data srid
    point.transform(4326)
    assert pytest.approx(unit.location.x, 0.0001) == 22.2632
    assert unit.service_nodes.all().count() == 1
    assert unit.services.all().count() == 1
    assert unit.services.all()[0].name == Importer.SERVICE_NAME  
    assert unit.service_nodes.all()[0].name == Importer.SERVICE_NODE_NAME  
    
