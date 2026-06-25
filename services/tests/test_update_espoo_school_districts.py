from datetime import datetime
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import MultiPolygon
from django.core.management import call_command
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)

from services.management.commands.school_district_import.espoo_school_district_importer import (  # noqa: E501
    EspooSchoolDistrictImporter,
)

FI_SOURCE = "GIS:Oppilaaksiottoalueet_suomenkielinen"
SV_SOURCE = "GIS:Oppilaaksiottoalueet_ruotsinkielinen_ala_aste"


@pytest.fixture
def municipality():
    municipality_type = AdministrativeDivisionType.objects.create(type="municipality")
    municipality_division = AdministrativeDivision.objects.create(
        type=municipality_type,
        name="Espoo",
        ocd_id="ocd-division/country:fi/kunta:espoo",
    )
    municipality = Municipality.objects.create(
        id="espoo", name="espoo", division=municipality_division
    )
    return municipality


def get_mock_data(source_type):
    mock_data = {
        FI_SOURCE: "services/tests/data/Oppilaaksiottoalueet_suomenkielinen.gml",
        SV_SOURCE: "services/tests/data/Oppilaaksiottoalueet_ruotsinkielinen_ala_aste.gml",  # noqa: E501
    }
    return mock_data[source_type]


@pytest.mark.django_db
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.espoo_school_district_importer.datetime"  # noqa: E501
)
def test_update_espoo_school_districts(mock_datetime, get_feature_mock, municipality):
    mock_datetime.today.return_value = datetime(2026, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    call_command("update_espoo_school_districts")

    # 2 source features -> current + next school year -> 4 divisions per type.
    assert (
        AdministrativeDivision.objects.filter(
            type__type="lower_comprehensive_school_district_fi"
        ).count()
        == 4
    )
    assert (
        AdministrativeDivision.objects.filter(
            type__type="upper_comprehensive_school_district_fi"
        ).count()
        == 4
    )
    assert (
        AdministrativeDivision.objects.filter(
            type__type="lower_comprehensive_school_district_sv"
        ).count()
        == 4
    )

    lower_fi = AdministrativeDivision.objects.get(
        origin_id="431976549_2026",
        type__type="lower_comprehensive_school_district_fi",
    )
    assert lower_fi.name == "Tapiolan oppilasalue"
    assert lower_fi.name_fi == "Tapiolan oppilasalue"
    assert lower_fi.municipality == municipality
    assert lower_fi.parent == municipality.division
    assert (
        lower_fi.ocd_id == "ocd-division/country:fi/kunta:espoo/"
        "oppilaaksiottoalue_alakoulu_fi:431976549_2026"
    )
    assert str(lower_fi.start) == "2026-08-01"
    assert str(lower_fi.end) == "2027-07-31"
    assert type(lower_fi.geometry.boundary) is MultiPolygon

    lower_fi_next = AdministrativeDivision.objects.get(
        origin_id="431976549_2027",
        type__type="lower_comprehensive_school_district_fi",
    )
    assert (
        lower_fi_next.ocd_id == "ocd-division/country:fi/kunta:espoo/"
        "oppilaaksiottoalue_alakoulu_fi:431976549_2027"
    )
    assert str(lower_fi_next.start) == "2027-08-01"
    assert str(lower_fi_next.end) == "2028-07-31"

    upper_fi = AdministrativeDivision.objects.get(
        origin_id="431976549_2026",
        type__type="upper_comprehensive_school_district_fi",
    )
    assert (
        upper_fi.ocd_id == "ocd-division/country:fi/kunta:espoo/"
        "oppilaaksiottoalue_ylakoulu_fi:431976549_2026"
    )

    lower_sv = AdministrativeDivision.objects.get(
        origin_id="495230929_2026",
        type__type="lower_comprehensive_school_district_sv",
    )
    assert lower_sv.name_sv == "Lagstads skola"
    assert lower_sv.name is None
    assert (
        lower_sv.ocd_id == "ocd-division/country:fi/kunta:espoo/"
        "oppilaaksiottoalue_alakoulu_sv:495230929_2026"
    )


@pytest.mark.django_db
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.espoo_school_district_importer.datetime"  # noqa: E501
)
def test_update_espoo_school_districts_removes_old_data(
    mock_datetime, get_feature_mock, municipality
):
    """Existing Espoo divisions should be removed before re-importing."""
    mock_datetime.today.return_value = datetime(2026, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    stale_type = AdministrativeDivisionType.objects.create(
        type="lower_comprehensive_school_district_fi"
    )
    AdministrativeDivision.objects.create(
        type=stale_type,
        origin_id="stale",
        name="Stale district",
        municipality=municipality,
    )

    call_command("update_espoo_school_districts")

    assert not AdministrativeDivision.objects.filter(origin_id="stale").exists()
    assert (
        AdministrativeDivision.objects.filter(
            type__type="lower_comprehensive_school_district_fi"
        ).count()
        == 4
    )


@pytest.mark.django_db
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.espoo_school_district_importer.datetime"  # noqa: E501
)
def test_update_espoo_school_districts_removes_obsolete_swedish_upper(
    mock_datetime, get_feature_mock, municipality
):
    """
    Swedish upper comprehensive districts are no longer imported, but existing
    Espoo data for them must still be removed.
    """
    mock_datetime.today.return_value = datetime(2026, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    obsolete_type = AdministrativeDivisionType.objects.create(
        type="upper_comprehensive_school_district_sv"
    )
    AdministrativeDivision.objects.create(
        type=obsolete_type,
        origin_id="obsolete",
        name="Obsolete sv upper district",
        municipality=municipality,
    )

    call_command("update_espoo_school_districts")

    assert not AdministrativeDivision.objects.filter(
        type__type="upper_comprehensive_school_district_sv"
    ).exists()


@pytest.mark.django_db
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.espoo_school_district_importer.datetime"  # noqa: E501
)
def test_update_espoo_does_not_remove_other_municipality_data(
    mock_datetime, get_feature_mock, municipality
):
    """Divisions of other municipalities sharing a type must be preserved."""
    mock_datetime.today.return_value = datetime(2026, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    helsinki_type = AdministrativeDivisionType.objects.create(type="municipality_hki")
    helsinki_division = AdministrativeDivision.objects.create(
        type=helsinki_type,
        name="Helsinki",
        ocd_id="ocd-division/country:fi/kunta:helsinki",
    )
    helsinki = Municipality.objects.create(
        id="helsinki", name="helsinki", division=helsinki_division
    )
    shared_type = AdministrativeDivisionType.objects.create(
        type="lower_comprehensive_school_district_fi"
    )
    AdministrativeDivision.objects.create(
        type=shared_type,
        origin_id="hki-1",
        name="Helsinki district",
        municipality=helsinki,
    )

    call_command("update_espoo_school_districts")

    assert AdministrativeDivision.objects.filter(
        origin_id="hki-1", municipality=helsinki
    ).exists()


@pytest.mark.parametrize(
    "today, expected",
    [
        (datetime(2026, 8, 1), [2026, 2027]),
        (datetime(2026, 12, 31), [2026, 2027]),
        (datetime(2026, 7, 31), [2025, 2026]),
        (datetime(2026, 1, 1), [2025, 2026]),
    ],
)
@patch(
    "services.management.commands.school_district_import.espoo_school_district_importer.datetime"  # noqa: E501
)
def test_get_school_year_start_years(mock_datetime, today, expected):
    mock_datetime.today.return_value = today
    assert EspooSchoolDistrictImporter.get_school_year_start_years() == expected
