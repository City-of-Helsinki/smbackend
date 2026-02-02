from unittest.mock import patch

import pytest
from django.core.management import call_command
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)


@pytest.fixture
def mock_parking_payzones_data():
    """Fixture for standard parking payzones with geometry."""
    return [
        {
            "geometry": {
                "coordinates": [
                    [
                        [25.038330550685124, 60.29497921873359],
                        [25.037180473305117, 60.29487636307983],
                        [25.036827917541686, 60.29429636983492],
                        [25.035635781656623, 60.294509434771044],
                        [25.0346088916754, 60.29254891106162],
                        [25.040769788807683, 60.291589437497],
                        [25.04022566806205, 60.29036550511179],
                        [25.042305325413064, 60.290149463457354],
                        [25.043072950077036, 60.29013333869665],
                        [25.04724510980411, 60.29261738435491],
                        [25.048514262487213, 60.29197399505413],
                        [25.04919074613015, 60.29229259744652],
                        [25.047275666908973, 60.293357603681955],
                        [25.04674651339548, 60.29396094884831],
                        [25.045984538606916, 60.29556359293879],
                        [25.0410192803547, 60.29602971167706],
                        [25.039211949420743, 60.296491443248684],
                        [25.038330550685124, 60.29497921873359],
                    ]
                ],
                "type": "Polygon",
            },
            "id": 1,
            "properties": {"maksullisu": "2 € / tunti", "objectid": 1},
            "type": "Feature",
        },
        {
            "geometry": {
                "coordinates": [
                    [
                        [24.850767495413702, 60.319266692115555],
                        [24.846091195840064, 60.317177969192386],
                        [24.83716953508307, 60.313142225053056],
                        [24.83840497595719, 60.31100208304065],
                        [24.841280862993386, 60.311415618492354],
                        [24.841642847963975, 60.31254006355655],
                        [24.84665891940124, 60.31491286135265],
                        [24.851120618528427, 60.31319172563568],
                        [24.852447081822483, 60.3140296975698],
                        [24.856279938251905, 60.31568335693376],
                        [24.859057217250353, 60.31626742568362],
                        [24.858139399790076, 60.317817202575384],
                        [24.85727295941106, 60.318502833518636],
                        [24.85597413934648, 60.31811439861645],
                        [24.85421957257933, 60.31897565427159],
                        [24.853341061488837, 60.31942031741433],
                        [24.850767495413702, 60.319266692115555],
                    ]
                ],
                "type": "Polygon",
            },
            "id": 2,
            "properties": {"maksullisu": "1 € / tunti", "objectid": 2},
            "type": "Feature",
        },
    ]


@pytest.fixture
def mock_parking_payzones_null_geometry_data():
    """Fixture for parking payzones with null geometry."""
    return [
        {
            "geometry": None,
            "id": 3,
            "properties": {"maksullisu": "3 € / tunti", "objectid": 3},
            "type": "Feature",
        }
    ]


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_payzones.Command.get_features"
)
def test_import_parking_payzones(get_features_mock, mock_parking_payzones_data):
    get_features_mock.return_value = mock_parking_payzones_data
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
def test_delete_removed_parking_payzones(get_features_mock, mock_parking_payzones_data):
    get_features_mock.return_value = mock_parking_payzones_data
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
def test_skip_parking_payzone_with_no_geometry(
    get_features_mock, mock_parking_payzones_null_geometry_data
):
    get_features_mock.return_value = mock_parking_payzones_null_geometry_data
    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_payzone")

    assert AdministrativeDivision.objects.count() == 0
    call_command("update_vantaa_parking_payzones")
    assert AdministrativeDivision.objects.count() == 0
