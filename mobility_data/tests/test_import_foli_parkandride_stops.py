from unittest.mock import patch

import pytest

from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_json_data


@pytest.mark.django_db
@patch("mobility_data.importers.utils.fetch_json")
def test_import_foli_stops(fetch_json_mock, municipalities):
    from mobility_data.importers.foli_parkandride_stop import (
        FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME,
        FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME,
        get_parkandride_stop_objects,
        save_to_database,
    )

    fetch_json_mock.return_value = get_test_fixture_json_data(
        "foli_parkandride_stops.json"
    )
    car_stops, bike_stops = get_parkandride_stop_objects()
    save_to_database(car_stops, FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME)
    save_to_database(bike_stops, FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME)

    cars_stops_content_type = ContentType.objects.get(
        name=FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME
    )
    bikes_stops_content_type = ContentType.objects.get(
        name=FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME
    )

    assert cars_stops_content_type
    assert bikes_stops_content_type
    # Fixture data contains two park and ride stops for cars and bikes.
    assert MobileUnit.objects.filter(content_type=cars_stops_content_type).count() == 2
    assert MobileUnit.objects.filter(content_type=bikes_stops_content_type).count() == 2
    # Test Föli park and ride cars stop
    lieto_centre = MobileUnit.objects.get(name_en="Lieto centre, K-Supermarket Lietori")
    assert lieto_centre.content_type == cars_stops_content_type
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
    assert raisio_st1.content_type == bikes_stops_content_type
    assert raisio_st1.name_fi == "St1 Raisio"
    assert raisio_st1.name_sv == "St1 Raisio"
    assert raisio_st1.address_zip == "21200"
    assert raisio_st1.description == "St1 Raisio\nKirkkoväärtinkuja 2, 21200"
    assert raisio_st1.municipality.name == "Raisio"
    assert raisio_st1.address_fi == "Kirkkoväärtinkuja 2"
    assert raisio_st1.address_sv == "Kirkkoväärtinkuja 2"
    assert raisio_st1.address_en == "Kirkkoväärtinkuja 2"
