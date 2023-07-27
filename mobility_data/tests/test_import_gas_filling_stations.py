from unittest.mock import patch

import pytest

from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_json_data


@pytest.mark.django_db
@patch("mobility_data.importers.gas_filling_station.get_json_data")
def test_importer(get_json_data_mock, municipalities):
    from mobility_data.importers.gas_filling_station import (
        CONTENT_TYPE_NAME,
        get_filtered_gas_filling_station_objects,
    )

    get_json_data_mock.return_value = get_test_fixture_json_data(
        "gas_filling_stations.json"
    )
    objects = get_filtered_gas_filling_station_objects()
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    num_created, num_deleted = save_to_database(objects, content_type)
    # Two will be created as One item in the fixture data locates outside Southwest Finland
    assert num_created == 2
    assert num_deleted == 0
    assert ContentType.objects.filter(type_name=CONTENT_TYPE_NAME).count() == 1
    assert (
        MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count()
        == 2
    )
    assert MobileUnit.objects.get(name="Raisio Kuninkoja")
    unit = MobileUnit.objects.get(name="Turku Satama")
    assert unit.address == "Tuontiväylä 42 abc 1-2"
    assert unit.address_zip == "20200"
    assert unit.municipality.name == "Turku"
    # Transform to source data srid
    unit.geometry.transform(3857)
    assert pytest.approx(unit.geometry.x, 0.0000000001) == 2472735.3962113541
    assert unit.extra["operator"] == "Gasum"
