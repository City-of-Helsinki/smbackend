import json
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import MultiPolygon
from django.core.management import call_command
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)


def get_mock_data(geometry=True):
    if geometry:
        file_path = "services/tests/data/vantaa_parking_areas.json"
    else:
        file_path = "services/tests/data/vantaa_parking_areas_null_geometry.json"
    with open(file_path, "r") as json_file:
        contents = json.load(json_file)
    return contents.get("features")


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_areas.DATA_SOURCES",
    [
        {
            "type": "parking_area",
            "service_url": "https://url",
            "layer_name": "Pysäköintialueet MUOKATTAVA",
            "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/pysakointipaikka-alue:",
        }
    ],
)
@patch("restapi.FeatureService")
def test_update_parking_areas(mock_feature_service):
    # Mock the FeatureService and its layer and features
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = get_mock_data()

    municipality = Municipality.objects.create(id="vantaa", name="Vantaa")
    division_type = AdministrativeDivisionType.objects.create(type="parking_area")

    assert AdministrativeDivision.objects.count() == 0

    call_command("update_vantaa_parking_areas")

    obj_1 = AdministrativeDivision.objects.get(origin_id=1)
    obj_2 = AdministrativeDivision.objects.get(origin_id=2)

    assert AdministrativeDivision.objects.count() == 2

    assert obj_1.name_fi == "Lyhytaikainen"
    assert obj_1.type == division_type
    assert obj_1.municipality == municipality
    assert type(obj_1.geometry.boundary) is MultiPolygon

    assert obj_2.name_fi == "Ei rajoitusta"
    assert obj_2.type == division_type
    assert obj_2.municipality == municipality
    assert type(obj_2.geometry.boundary) is MultiPolygon


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_areas.DATA_SOURCES",
    [
        {
            "type": "parking_area",
            "service_url": "https://url",
            "layer_name": "Pysäköintialueet MUOKATTAVA",
            "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/pysakointipaikka-alue:",
        }
    ],
)
@patch("restapi.FeatureService")
def test_delete_removed_parking_areas(mock_feature_service):
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = get_mock_data()

    municipality = Municipality.objects.create(id="vantaa", name="Vantaa")
    division_type = AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    # Add a parking area that is not in the source data
    AdministrativeDivision.objects.create(
        origin_id="3", type=division_type, municipality=municipality
    )

    assert (
        AdministrativeDivision.objects.filter(
            type=division_type, municipality=municipality
        ).count()
        == 3
    )

    call_command("update_vantaa_parking_areas")

    assert (
        AdministrativeDivision.objects.filter(
            type=division_type, municipality=municipality
        ).count()
        == 2
    )
    assert not AdministrativeDivision.objects.filter(origin_id="3").exists()


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_areas.DATA_SOURCES",
    [
        {
            "type": "parking_area",
            "service_url": "https://url",
            "layer_name": "Pysäköintialueet MUOKATTAVA",
            "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/pysakointipaikka-alue:",
        }
    ],
)
@patch("restapi.FeatureService")
def test_skip_parking_areas_with_no_geometry(mock_feature_service):
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = get_mock_data(geometry=False)

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    assert AdministrativeDivision.objects.count() == 0
    call_command("update_vantaa_parking_areas")
    assert AdministrativeDivision.objects.count() == 0
