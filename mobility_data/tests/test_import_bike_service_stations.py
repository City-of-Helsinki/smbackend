from unittest.mock import patch

import pytest

from mobility_data.importers.utils import (
    get_content_type_config,
    get_or_create_content_type_from_config,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_data_layer


@pytest.mark.django_db
@patch("mobility_data.importers.bike_service_stations.get_data_layer")
def test_import_bike_service_stations(get_data_layer_mock):
    from mobility_data.importers.bike_service_stations import (
        CONTENT_TYPE_NAME,
        get_bike_service_station_objects,
    )

    get_data_layer_mock.return_value = get_test_fixture_data_layer(
        "bike_service_stations.geojson"
    )
    objects = get_bike_service_station_objects()
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
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
    kupittaankentta = MobileUnit.objects.get(name="Kupittaankenttä")
    assert kupittaankentta.name_sv == "Kuppisplan"
    assert kupittaankentta.name_en == "Kupittaa court"
    assert kupittaankentta.address == "Uudenmaankatu 18"
    assert kupittaankentta.address_sv == "Nylandsgatan 18"
    assert kupittaankentta.address_en == "Uudenmaankatu 18"
    assert "pyöränpumpun ja kaksi monitoimityökalua" in kupittaankentta.description
    assert "cykelpump och två multiverktyg" in kupittaankentta.description_sv
    assert (
        "includes bicycle pump and two multifunctional tools"
        in kupittaankentta.description_en
    )
    assert kupittaankentta.extra["in_terrain"] == "Ei"
    assert kupittaankentta.extra["additional_details"] == "Merkki Care4bikes"
    roola = MobileUnit.objects.get(name="Röölä")
    assert roola.name_sv == "Röölä"
    assert roola.name_en == "Röölä"
    assert roola.extra["in_terrain"] == "Kyllä"
    # Test that dublicates are not created
    get_data_layer_mock.return_value = get_test_fixture_data_layer(
        "bike_service_stations.geojson"
    )
    objects = get_bike_service_station_objects()
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 0
    assert num_deleted == 0
    assert ContentType.objects.filter(type_name=CONTENT_TYPE_NAME).count() == 1
    assert (
        MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count()
        == 3
    )
