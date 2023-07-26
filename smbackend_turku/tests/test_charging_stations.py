import logging
from datetime import datetime
from unittest.mock import patch

import pytest
import pytz
from django.conf import settings

from services.models import Service, ServiceNode, Unit
from smbackend_turku.importers.stations import import_charging_stations
from smbackend_turku.importers.utils import get_external_source_config


@pytest.mark.django_db
@patch("mobility_data.importers.charging_stations.get_csv_file_name")
def test_charging_stations_import(
    get_csv_file_name_mock,
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
    config = get_external_source_config("gas_filling_stations")

    # create root servicenode to which the imported service_node will connect
    ServiceNode.objects.create(
        id=42, name="Vapaa-aika", last_modified_time=datetime.now(utc_timezone)
    )
    file_name = f"{settings.BASE_DIR}/mobility_data/tests/data/charging_stations.csv"
    get_csv_file_name_mock.return_value = file_name
    import_charging_stations(
        logger=logger,
        config=config,
    )
    assert Unit.objects.all().count() == 3
    Service.objects.all().count() == 1
    service = Service.objects.first()
    assert service.name == config["service"]["name"]["fi"]
    assert service.name_sv == config["service"]["name"]["sv"]
    assert service.name_en == config["service"]["name"]["en"]
    service_node = ServiceNode.objects.get(name=config["service_node"]["name"]["fi"])
    assert service_node.name_sv == config["service_node"]["name"]["sv"]
    assert service_node.name_en == config["service_node"]["name"]["en"]
    aimopark = Unit.objects.get(name="Aimopark, Yliopistonkatu 29")
    assert aimopark.name_sv == "Aimopark, Universitetsgatan 29"
    assert aimopark.street_address == "Yliopistonkatu 29"
    assert aimopark.street_address_sv == "Universitetsgatan 29"
    assert aimopark.municipality.name == "Turku"
    assert aimopark.address_zip == "20100"
    assert aimopark.root_service_nodes == "42"
    assert aimopark.services.count() == 1
    assert aimopark.services.first() == service
