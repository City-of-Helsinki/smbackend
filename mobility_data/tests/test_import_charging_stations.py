from unittest.mock import patch

import pytest
from munigeo.models import Address

from mobility_data.importers.charging_stations import CHARGING_STATION_SERVICE_NAMES
from mobility_data.importers.utils import (
    get_content_type_config,
    get_or_create_content_type_from_config,
    get_root_dir,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit


@pytest.mark.django_db
@patch("mobility_data.importers.charging_stations.get_csv_file_name")
def test_import_charging_stations(
    get_csv_file_name_mock,
    municipalities,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    from mobility_data.importers.charging_stations import (
        CONTENT_TYPE_NAME,
        get_charging_station_objects,
    )

    file_name = f"{get_root_dir()}/mobility_data/tests/data/charging_stations.csv"
    get_csv_file_name_mock.return_value = file_name
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    objects = get_charging_station_objects()
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 3
    assert num_deleted == 0
    assert ContentType.objects.filter(type_name=CONTENT_TYPE_NAME).count() == 1
    assert (
        MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count()
        == 3
    )
    config = get_content_type_config(CONTENT_TYPE_NAME)
    content_type = ContentType.objects.get(type_name=CONTENT_TYPE_NAME)
    content_type.name_fi = config["name"]["fi"]
    content_type.name_sv = config["name"]["sv"]
    content_type.name_en = config["name"]["en"]
    aimopark = MobileUnit.objects.get(name="Aimopark, Yliopistonkatu 29")
    assert aimopark.address == "Yliopistonkatu 29"
    assert aimopark.address_sv == "Universitetsgatan 29"
    assert aimopark.address_en == "Yliopistonkatu 29"
    yliopistonkatu_29 = Address.objects.get(full_name_fi="Yliopistonkatu 29")
    assert (
        aimopark.geometry.equals_exact(yliopistonkatu_29.location, tolerance=70) is True
    )
    chargers = aimopark.extra["chargers"]
    assert len(chargers) == 2
    assert chargers[0]["plug"] == "Type 2"
    assert chargers[0]["power"] == "22"
    assert chargers[0]["number"] == "2"
    assert aimopark.extra["payment"] == "Sisältyy hintaan"
    assert aimopark.extra["charge_target"] == "Julkinen"
    assert aimopark.extra["method_of_use"] == "P-paikan hintaan"
    turku_energia = MobileUnit.objects.get(name="Turku Energia, Aninkaistenkatu 20")
    assert turku_energia.extra["administrator"]["fi"] == "Turku Energia"
    assert turku_energia.extra["administrator"]["sv"] == "Åbo Energi"
    assert turku_energia.extra["administrator"]["en"] == "Turku Energia"
    # Test that charging station without administrator gets the name from service
    name = f"{CHARGING_STATION_SERVICE_NAMES['fi']}, Ratapihankatu 53"
    ratapihankatu = MobileUnit.objects.get(name=name)
    assert ratapihankatu
    assert (
        ratapihankatu.name_sv
        == f"{CHARGING_STATION_SERVICE_NAMES['sv']}, Bangårdsgatan 53"
    )
    assert (
        ratapihankatu.name_en
        == f"{CHARGING_STATION_SERVICE_NAMES['en']}, Ratapihankatu 53"
    )
    # Test that dublicates are not created
    get_csv_file_name_mock.return_vale = file_name
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    objects = get_charging_station_objects()
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 0
    assert num_deleted == 0
    assert ContentType.objects.filter(type_name=CONTENT_TYPE_NAME).count() == 1
    assert (
        MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count()
        == 3
    )
