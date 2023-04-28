from unittest.mock import patch

import pytest

from mobility_data.importers.utils import (
    get_content_type_config,
    get_or_create_content_type_from_config,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_json_data


@pytest.mark.django_db
@patch("mobility_data.importers.utils.fetch_json")
def test_import_foli_stops(fetch_json_mock, municipalities):
    from mobility_data.importers.foli_parkandride_stop import (
        FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME,
        FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME,
        get_parkandride_bike_stop_objects,
        get_parkandride_car_stop_objects,
    )

    fetch_json_mock.return_value = get_test_fixture_json_data(
        "foli_parkandride_stops.json"
    )

    car_stops = get_parkandride_car_stop_objects()
    content_type = get_or_create_content_type_from_config(
        FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME
    )
    num_created, num_deleted = save_to_database(car_stops, content_type)
    assert num_created == 2
    assert num_deleted == 0
    bike_stops = get_parkandride_bike_stop_objects()
    content_type = get_or_create_content_type_from_config(
        FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME
    )
    num_created, num_deleted = save_to_database(bike_stops, content_type)
    assert num_created == 2
    assert num_deleted == 0
    cars_stops_content_type = ContentType.objects.get(
        type_name=FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME
    )
    config = get_content_type_config(FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME)
    cars_stops_content_type.name_fi = config["name"]["fi"]
    cars_stops_content_type.name_sv = config["name"]["sv"]
    cars_stops_content_type.name_en = config["name"]["en"]

    bikes_stops_content_type = ContentType.objects.get(
        type_name=FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME
    )
    config = get_content_type_config(FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME)
    bikes_stops_content_type.name_fi = config["name"]["fi"]
    bikes_stops_content_type.name_sv = config["name"]["sv"]
    bikes_stops_content_type.name_en = config["name"]["en"]
    # Fixture data contains two park and ride stops for cars and bikes.
    assert MobileUnit.objects.filter(content_types=cars_stops_content_type).count() == 2
    assert (
        MobileUnit.objects.filter(content_types=bikes_stops_content_type).count() == 2
    )
    # Test Föli park and ride cars stop
    lieto_centre = MobileUnit.objects.get(name_en="Lieto centre, K-Supermarket Lietori")
    assert lieto_centre.content_types.all().count() == 1
    assert lieto_centre.content_types.first() == cars_stops_content_type
    assert lieto_centre.name_fi == "Lieto Keskusta, K-Supermarket Lietorin piha"
    assert lieto_centre.name_sv == "Lundo centrum, K-Supermarket Lietori"
    assert lieto_centre.address_zip == "21420"
    assert (
        lieto_centre.description
        == "Lieto Keskusta, K-Supermarket Lietorin piha\nHyvättyläntie 2, 21420"
    )
    assert lieto_centre.address_fi == "Hyvättyläntie 2"
    assert lieto_centre.address_sv == "Hyvättyläntie 2"
    assert lieto_centre.address_en == "Hyvättyläntie 2"
    assert lieto_centre.municipality.name == "Lieto"

    # Test Föli park and ride bikes stop
    raisio_st1 = MobileUnit.objects.get(name_en="St1 Raisio")
    assert raisio_st1.content_types.first() == bikes_stops_content_type
    assert raisio_st1.name_fi == "St1 Raisio"
    assert raisio_st1.name_sv == "St1 Raisio"
    assert raisio_st1.address_zip == "21200"
    assert raisio_st1.description == "St1 Raisio\nKirkkoväärtinkuja 2, 21200"
    assert raisio_st1.municipality.name == "Raisio"
    assert raisio_st1.address_fi == "Kirkkoväärtinkuja 2"
    assert raisio_st1.address_sv == "Kirkkoväärtinkuja 2"
    assert raisio_st1.address_en == "Kirkkoväärtinkuja 2"

    json_data = get_test_fixture_json_data("foli_parkandride_stops.json")
    # Add only One cars parkandride stop
    json_data["features"] = [json_data["features"][0]]
    fetch_json_mock.return_value = json_data
    car_stops = get_parkandride_car_stop_objects()
    content_type = get_or_create_content_type_from_config(
        FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME
    )
    # Test that obsolete mobile units are deleted and duplicates are not created
    num_created, num_deleted = save_to_database(car_stops, content_type)
    assert num_created == 0
    assert num_deleted == 1
    assert MobileUnit.objects.filter(content_types=cars_stops_content_type).count() == 1
    assert raisio_st1.id == MobileUnit.objects.get(name_en="St1 Raisio").id
