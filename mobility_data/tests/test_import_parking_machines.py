from unittest.mock import patch

import pytest

from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_json_data


@pytest.mark.django_db
@patch("mobility_data.importers.parking_machines.get_json_data")
def test_import_parking_machines(get_json_data_mock):
    from mobility_data.importers import parking_machines

    get_json_data_mock.return_value = get_test_fixture_json_data(
        "parking_machines.geojson"
    )
    objects = parking_machines.get_parking_machine_objects()
    parking_machines.save_to_database(objects)
    assert ContentType.objects.first().name == parking_machines.CONTENT_TYPE_NAME
    assert MobileUnit.objects.count() == 3
    satamakatu = MobileUnit.objects.first()
    assert satamakatu.content_types.all().count() == 1
    assert satamakatu.content_types.first() == ContentType.objects.first()
    assert satamakatu.address == "Satamakatu 18 vp"
    assert satamakatu.address_sv == "Hamngatan 18 me"
    assert satamakatu.address_en == "Satamakatu 18 vp"
    assert satamakatu.extra["Malli"] == "CWT-C Touch"
    assert satamakatu.extra["Muuta"] == "16 € / 26 h"
    assert satamakatu.extra["Taksa/h"] == 1.3
    assert satamakatu.extra["Max.aika"] is None
    assert satamakatu.extra["Asennettu"] == "15.10.2022"
    assert satamakatu.extra["Valmistaja"] == "Cale"
    assert satamakatu.extra["Virta"]["fi"] == "Verkkovirta"
    assert satamakatu.extra["Virta"]["sv"] == "Nät"
    assert satamakatu.extra["Virta"]["en"] == "Mains"
    assert satamakatu.extra["Näyttö"]["fi"] == '9", kosketus'
    assert satamakatu.extra["Näyttö"]["sv"] == '9", pekskärm'
    assert satamakatu.extra["Näyttö"]["en"] == '9", touch screen'
    assert satamakatu.extra["Omistaja"]["fi"] == "Turun kaupunki"
    assert satamakatu.extra["Omistaja"]["sv"] == "Åbo stad"
    assert satamakatu.extra["Omistaja"]["en"] == "City of Turku"
    assert satamakatu.extra["Sijainti"]["fi"] == "Katuosa"
    assert satamakatu.extra["Sijainti"]["sv"] == "Gata"
    assert satamakatu.extra["Sijainti"]["en"] == "On-street"
    assert satamakatu.extra["Maksuvyöhyke"]["fi"] == "Satama"
    assert satamakatu.extra["Maksuvyöhyke"]["sv"] == "Hamn"
    assert satamakatu.extra["Maksuvyöhyke"]["en"] == "Harbour"
    assert satamakatu.extra["Maksutapa"]["fi"] == "Kolikko, kortti, lähimaksu"
    assert satamakatu.extra["Maksutapa"]["sv"] == "Mynt, kort, kontaktlös"
    assert satamakatu.extra["Maksutapa"]["en"] == "Coin, card, contactless"
