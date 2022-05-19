import logging
from datetime import datetime

import pytest
import pytz

from services.models import Service, ServiceNode, Unit
from smbackend_turku.importers.constants import (
    CHARGING_STATION_SERVICE_NAMES,
    CHARGING_STATION_SERVICE_NODE_NAMES,
)
from smbackend_turku.importers.stations import import_charging_stations


@pytest.mark.django_db
def test_charging_stations_import(
    municipality,
    administrative_division,
    administrative_division_type,
    administrative_division_geometry,
    streets,
    address,
    postal_code_areas,
):
    logger = logging.getLogger(__name__)
    utc_timezone = pytz.timezone("UTC")
    # create root servicenode to which the imported service_node will connect
    ServiceNode.objects.create(
        id=42, name="TestRoot", last_modified_time=datetime.now(utc_timezone)
    )

    import_charging_stations(
        logger=logger,
        root_service_node_name="TestRoot",
        test_data="charging_stations.csv",
    )
    assert Unit.objects.all().count() == 3
    Service.objects.all().count() == 1
    service = Service.objects.all()[0]
    assert service.name == CHARGING_STATION_SERVICE_NAMES["fi"]
    assert service.name_sv == CHARGING_STATION_SERVICE_NAMES["sv"]
    assert service.name_en == CHARGING_STATION_SERVICE_NAMES["en"]
    service_node = ServiceNode.objects.get(
        name=CHARGING_STATION_SERVICE_NODE_NAMES["fi"]
    )
    assert service_node.name_sv == CHARGING_STATION_SERVICE_NODE_NAMES["sv"]
    assert service_node.name_en == CHARGING_STATION_SERVICE_NODE_NAMES["en"]
    aimopark = Unit.objects.get(name="Aimopark, Yliopistonkatu 29")
    assert aimopark.name_sv == "Aimopark, Universitetsgatan 29"
    assert aimopark.street_address == "Yliopistonkatu 29"
    assert aimopark.street_address_sv == "Universitetsgatan 29"
    assert aimopark.municipality.name == "Turku"
    assert aimopark.address_zip == "20100"
    assert aimopark.description_sv == CHARGING_STATION_SERVICE_NAMES["sv"]
    assert aimopark.root_service_nodes == "42"
    assert aimopark.services.count() == 1
    assert aimopark.services.all()[0] == service
