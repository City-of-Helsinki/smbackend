import json
from unittest.mock import patch

import pytest
from django.core.management import call_command
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)


def get_mock_data(geometry=True):
    if geometry:
        file_path = "services/tests/data/vantaa_parking_payzones.json"
    else:
        file_path = "services/tests/data/vantaa_parking_payzones_null_geometry.json"
    with open(file_path, "r") as json_file:
        contents = json.load(json_file)
    return contents.get("features")


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_payzones.Command.get_features"
)
def test_import_parking_payzones(get_features_mock):
    get_features_mock.return_value = get_mock_data()
    municipality = Municipality.objects.create(id="vantaa", name="Vantaa")
    division_type = AdministrativeDivisionType.objects.create(type="parking_payzone")

    assert (
        AdministrativeDivision.objects.filter(
            type=division_type, municipality=municipality
        ).count()
        == 0
    )

    call_command("update_vantaa_parking_payzones")
    zone_1 = AdministrativeDivision.objects.get(origin_id="1")
    zone_2 = AdministrativeDivision.objects.get(origin_id="2")

    assert (
        AdministrativeDivision.objects.filter(
            type=division_type, municipality=municipality
        ).count()
        == 2
    )
    assert zone_1.name_fi == "2 € / tunti"
    assert zone_2.name_fi == "1 € / tunti"
    assert zone_1.name_sv == "2 € / timme"
    assert zone_2.name_sv == "1 € / timme"
    assert zone_1.name_en == "2 € / hour"
    assert zone_2.name_en == "1 € / hour"
    assert (
        zone_1.ocd_id == "ocd-division/country:fi/kunta:vantaa/pysakointimaksuvyohyke:1"
    )
    assert (
        zone_2.ocd_id == "ocd-division/country:fi/kunta:vantaa/pysakointimaksuvyohyke:2"
    )
    assert zone_1.geometry is not None
    assert zone_2.geometry is not None


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_payzones.Command.get_features"
)
def test_delete_removed_parking_payzones(get_features_mock):
    get_features_mock.return_value = get_mock_data()
    municipality = Municipality.objects.create(id="vantaa", name="Vantaa")
    division_type = AdministrativeDivisionType.objects.create(type="parking_payzone")
    call_command("update_vantaa_parking_payzones")

    # Add a parking payzone that is not in the source data
    AdministrativeDivision.objects.create(
        origin_id="3", type=division_type, municipality=municipality
    )
    assert (
        AdministrativeDivision.objects.filter(
            type=division_type, municipality=municipality
        ).count()
        == 3
    )

    call_command("update_vantaa_parking_payzones")

    assert (
        AdministrativeDivision.objects.filter(
            type=division_type, municipality=municipality
        ).count()
        == 2
    )
    assert not AdministrativeDivision.objects.filter(origin_id="3").exists()


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_payzones.Command.get_features"
)
def test_skip_parking_payzone_with_no_geometry(get_features_mock):
    get_features_mock.return_value = get_mock_data(geometry=False)
    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_payzone")

    assert AdministrativeDivision.objects.count() == 0
    call_command("update_vantaa_parking_payzones")
    assert AdministrativeDivision.objects.count() == 0
