from unittest.mock import patch

import pytest

from mobility_data.importers.utils import (
    get_content_type_config,
    get_or_create_content_type_from_config,
    get_root_dir,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit


@pytest.mark.django_db
@patch("mobility_data.importers.parking_garages.get_full_csv_file_name")
def test_import_parking_garages(
    get_full_csv_file_name_mock,
    municipalities,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    from mobility_data.importers.parking_garages import (
        CONTENT_TYPE_NAME,
        get_parking_garage_objects,
    )

    file_name = f"{get_root_dir()}/mobility_data/tests/data/parkkihallit_fixtures.csv"
    get_full_csv_file_name_mock.return_value = file_name
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    objects = get_parking_garage_objects()
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 2
    assert num_deleted == 0
    assert ContentType.objects.filter(type_name=CONTENT_TYPE_NAME).count() == 1
    assert (
        MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count()
        == 2
    )
    config = get_content_type_config(CONTENT_TYPE_NAME)
    content_type = ContentType.objects.get(type_name=CONTENT_TYPE_NAME)
    content_type.name_fi = config["name"]["fi"]
    content_type.name_sv = config["name"]["sv"]
    content_type.name_en = config["name"]["en"]

    auriga = MobileUnit.objects.get(name="Auriga")
    assert auriga.name_sv == "Auriga"
    assert auriga.name_en == "Auriga"
    assert auriga.address_fi == "Juhana Herttuan puistokatu 21"
    assert auriga.address_sv == "Hertig Johans parkgata 21"
    assert auriga.address_en == "Juhana Herttuan puistokatu 21"
    assert auriga.municipality.name == "Turku"
    assert auriga.extra["parking_spaces"] == 330
    assert auriga.extra["disabled_spaces"] == 2
    assert auriga.extra["charging_stations"] == "2 x Type 2 22 kW"
    assert (
        auriga.extra["services"]["fi"]
        == "Apuvirta, hissi, liikkumisesteisen pysäköintipaikka, sähköauton latauspiste"
    )
    assert (
        auriga.extra["services"]["sv"]
        == "Elbilsladdning, hiss, parkeringsplats för funktionshindrade, startkablar"
    )
    assert (
        auriga.extra["services"]["en"]
        == "Disabled parking, elevator, EV charging, jump leads"
    )
