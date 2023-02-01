from unittest.mock import patch

import pytest

from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_data_layer


@pytest.mark.django_db
@patch("mobility_data.importers.parking_machines.get_data_layer")
def test_import_parking_machines(get_data_layer_mock):
    from mobility_data.importers import parking_machines

    get_data_layer_mock.return_value = get_test_fixture_data_layer(
        "parking_machines.geojson"
    )
    objects = parking_machines.get_parking_machine_objects()
    parking_machines.save_to_database(objects)
    assert ContentType.objects.first().name == parking_machines.CONTENT_TYPE_NAME
    assert MobileUnit.objects.count() == 3
    satamakatu = MobileUnit.objects.first()
    assert satamakatu.content_type == ContentType.objects.first()
    assert satamakatu.address == "Satamakatu 18 vp"
    assert satamakatu.extra["Malli"] == "CWT-C Touch"
    assert satamakatu.extra["Muuta"] == "16 € / 26 h"
    assert satamakatu.extra["Virta"] == "Verkkovirta"
    assert satamakatu.extra["Taksa/h"] == 1.3
    assert satamakatu.extra["Max.aika"] is None
    assert satamakatu.extra["Näyttö"] == '9", kosketus'
    assert satamakatu.extra["Omistaja"] == "Turun kaupunki"
    assert satamakatu.extra["Sijainti"] == "Katuosa"
    assert satamakatu.extra["Asennettu"] == "15.10.2022"
    assert satamakatu.extra["Maksutapa"] == "Kolikko, kortti, lähimaksu"
    assert satamakatu.extra["Valmistaja"] == "Cale"
    assert satamakatu.extra["Maksuvyöhyke"] is None
