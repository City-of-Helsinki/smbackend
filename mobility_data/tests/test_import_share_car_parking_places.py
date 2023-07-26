from unittest.mock import patch

import pytest

from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    get_root_dir,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit


@pytest.mark.django_db
@patch("mobility_data.importers.share_car_parking_places.get_geojson_file_name")
def test_import_car_share_parking_places(get_geojson_file_name_mock):
    from mobility_data.importers.share_car_parking_places import (
        CONTENT_TYPE_NAME,
        get_car_share_parking_place_objects,
    )

    file_name = (
        f"{get_root_dir()}/mobility_data/tests/data/share_car_parking_places.geojson"
    )
    get_geojson_file_name_mock.return_value = file_name
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    objects = get_car_share_parking_place_objects()
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 3
    assert ContentType.objects.filter(type_name=CONTENT_TYPE_NAME).count() == 1
    assert (
        MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count()
        == 3
    )
    linnankatu = MobileUnit.objects.get(
        name="Yhteiskäyttöautojen pysäköintipaikka, Linnankatu 29"
    )
    assert linnankatu.name_sv == "Bilpoolbilars parkeringsplats, Slottsgatan 29"
    assert linnankatu.name_en == "Parking place for car sharing cars, Linnankatu 29"
    assert linnankatu.address_fi == "Linnankatu 29"
    assert linnankatu.address_sv == "Slottsgatan 29"
    assert linnankatu.address_en == "Linnankatu 29"
    assert linnankatu.extra["Rajoit_lis"]["fi"] == "Lisäkilpi: Ei koske P-tunnuksella"
    assert linnankatu.extra["Rajoit_lis"]["sv"] == "Gäller ej P-tecknet"
    assert linnankatu.extra["Rajoit_lis"]["en"] == "Z"
    assert linnankatu.extra["Kohde"] == "Linnankatu"
    assert linnankatu.extra["Saavutetta"] == "Vapaa pääsy"
    assert linnankatu.extra["Sähkölat"] is None
    assert linnankatu.extra["Paikkoja_y"] == "1"

    rautatientori = MobileUnit.objects.get(
        name="Yhteiskäyttöautojen pysäköintipaikka, Läntinen Pitkäkatu 26"
    )
    assert rautatientori.extra["Paikkoja_y"] == "2"
    rautatientori.extra["Invapaikko"] is None
