import logging
from datetime import datetime

import pytest
import pytz
from munigeo.models import Municipality

from services.models import Service, ServiceNode, Unit
from smbackend_turku.importers.bike_service_stations import import_bike_service_stations
from smbackend_turku.importers.constants import (
    BIKE_SERVICE_STATION_SERVICE_NAMES,
    BIKE_SERVICE_STATION_SERVICE_NODE_NAMES,
)


@pytest.mark.django_db
def test_bike_service_stations_import(
    municipality,
    administrative_division,
    administrative_division_type,
    administrative_division_geometry,
):
    logger = logging.getLogger(__name__)
    utc_timezone = pytz.timezone("UTC")
    # create root servicenode to which the imported service_node will connect
    ServiceNode.objects.create(
        id=42, name="TestRoot", last_modified_time=datetime.now(utc_timezone)
    )
    import_bike_service_stations(
        logger=logger,
        root_service_node_name="TestRoot",
        test_data="bike_service_stations.geojson",
    )
    assert Unit.objects.all().count() == 3
    Service.objects.all().count() == 1
    service = Service.objects.all()[0]
    assert service.name == BIKE_SERVICE_STATION_SERVICE_NAMES["fi"]
    assert service.name_sv == BIKE_SERVICE_STATION_SERVICE_NAMES["sv"]
    assert service.name_en == BIKE_SERVICE_STATION_SERVICE_NAMES["en"]
    service_node = ServiceNode.objects.get(
        name=BIKE_SERVICE_STATION_SERVICE_NODE_NAMES["fi"]
    )
    assert service_node.name_sv == BIKE_SERVICE_STATION_SERVICE_NODE_NAMES["sv"]
    assert service_node.name_en == BIKE_SERVICE_STATION_SERVICE_NODE_NAMES["en"]
    nauvo = Unit.objects.get(name="Nauvo")
    assert nauvo.name_sv == "Nagu"
    assert nauvo.name_en == "Nauvo"
    assert nauvo.street_address == "Nauvon ranta 6"
    assert nauvo.street_address_sv == "Nagu Strand 6"
    assert nauvo.street_address_en == "Nauvon ranta 6"
    assert nauvo.address_zip == "21660"
    assert nauvo.extra["in_terrain"] == "Kyllä"
    assert nauvo.extra["additional_details"] == "Merkki iBOMBO PRS SCANDIC"
    kupittaankentta = Unit.objects.get(name="Kupittaankenttä")
    assert kupittaankentta.municipality == Municipality.objects.get(id="turku")
    assert kupittaankentta.provider_type == 1
