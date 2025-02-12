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

from services.management.commands.school_district_import.school_district_importer import (
    SchoolDistrictImporter,
)


@pytest.fixture
def municipality():
    municipality_type = AdministrativeDivisionType.objects.create(type="municipality")
    municipality_division = AdministrativeDivision.objects.create(
        type=municipality_type,
        name="Helsinki",
        ocd_id="ocd-division/country:fi/kunta:helsinki",
    )
    municipality = Municipality.objects.create(
        id="helsinki", name="helsinki", division=municipality_division
    )
    return municipality


def get_mock_data(source_type):
    mock_data = {
        "avoindata:Esiopetusalue_suomi": "services/tests/data/Esiopetusalue_suomi.gml",
        "avoindata:Esiopetusalue_suomi_tuleva": "services/tests/data/Esiopetusalue_suomi_tuleva.gml",
        "avoindata:Opev_ooa_alaaste_suomi_tuleva": "services/tests/data/Opev_ooa_alaaste_suomi_tuleva.gml",
        "avoindata:Opev_ooa_alaaste_suomi_no_unit": "services/tests/data/Opev_ooa_alaaste_suomi_no_unit.gml",
        "avoindata:Esiopetusalue_suomi_broken": "services/tests/data/Esiopetusalue_suomi_broken.gml",
        "avoindata:Esiopetusalue_suomi_no_unit": "services/tests/data/Esiopetusalue_suomi_no_unit.gml",
    }
    return mock_data.get(source_type, "services/tests/data/Opev_ooa_alaaste_suomi.gml")


@pytest.mark.django_db
@patch(
    "services.management.commands.update_helsinki_school_districts.SCHOOL_DISTRICT_DATA",
    [
        {
            "source_type": "avoindata:Opev_ooa_alaaste_suomi",
            "division_type": "lower_comprehensive_school_district_fi",
            "ocd_id": "oppilaaksiottoalue_alakoulu",
        },
        {
            "source_type": "avoindata:Opev_ooa_alaaste_suomi_tuleva",
            "division_type": "lower_comprehensive_school_district_fi",
            "ocd_id": "oppilaaksiottoalue_alakoulu",
        },
    ],
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.school_district_importer.datetime"
)
def test_update_school_districts(mock_datetime, get_feature_mock, municipality):
    mock_datetime.today.return_value = datetime(2023, 1, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    assert not AdministrativeDivision.objects.filter(
        type__type="lower_comprehensive_school_district_fi"
    ).exists()

    call_command("update_helsinki_school_districts")

    assert (
        AdministrativeDivision.objects.filter(
            type__type="lower_comprehensive_school_district_fi"
        ).count()
        == 2
    )

    division_1 = AdministrativeDivision.objects.get(origin_id="111")
    assert division_1.name == "Testi peruskoulu 2024-2025"
    assert division_1.type.type == "lower_comprehensive_school_district_fi"
    assert division_1.municipality == municipality
    assert division_1.parent == municipality.division
    assert (
        division_1.ocd_id
        == "ocd-division/country:fi/kunta:helsinki/oppilaaksiottoalue_alakoulu:111"
    )
    assert division_1.service_point_id == "13"
    assert type(division_1.geometry.boundary) is MultiPolygon

    division_2 = AdministrativeDivision.objects.get(origin_id="222")
    assert division_2.name == "Testi peruskoulu 2023-2024"
    assert division_2.type.type == "lower_comprehensive_school_district_fi"
    assert division_2.municipality == municipality
    assert division_2.parent == municipality.division
    assert (
        division_2.ocd_id
        == "ocd-division/country:fi/kunta:helsinki/oppilaaksiottoalue_alakoulu:222"
    )
    assert division_2.service_point_id == "13"
    assert type(division_2.geometry.boundary) is MultiPolygon


@pytest.mark.django_db
@patch(
    "services.management.commands.update_helsinki_school_districts.SCHOOL_DISTRICT_DATA",
    [
        {
            "source_type": "avoindata:Opev_ooa_alaaste_suomi",
            "division_type": "lower_comprehensive_school_district_fi",
            "ocd_id": "oppilaaksiottoalue_alakoulu",
        },
        {
            "source_type": "avoindata:Opev_ooa_alaaste_suomi_tuleva",
            "division_type": "lower_comprehensive_school_district_fi",
            "ocd_id": "oppilaaksiottoalue_alakoulu",
        },
    ],
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.school_district_importer.datetime"
)
def test_update_school_districts_removes_school_year(
    mock_datetime, get_feature_mock, municipality
):
    """
    When date is between 1.8. and 15.12. the previous school year should be removed
    """
    mock_datetime.today.return_value = datetime(2024, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    call_command("update_helsinki_school_districts")
    assert (
        AdministrativeDivision.objects.filter(
            type__type="lower_comprehensive_school_district_fi"
        ).count()
        == 1
    )
    assert AdministrativeDivision.objects.filter(
        name="Testi peruskoulu 2024-2025"
    ).exists()


@pytest.mark.django_db
@patch(
    "services.management.commands.update_helsinki_preschool_districts.PRESCHOOL_DISTRICT_DATA",
    [
        {
            "source_type": "avoindata:Esiopetusalue_suomi",
            "division_type": "preschool_education_fi",
            "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
        },
        {
            "source_type": "avoindata:Esiopetusalue_suomi_tuleva",
            "division_type": "preschool_education_fi",
            "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
        },
    ],
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.school_district_importer.datetime"
)
def test_update_preschool_districts(mock_datetime, get_feature_mock, municipality):
    mock_datetime.today.return_value = datetime(2023, 1, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    assert not AdministrativeDivision.objects.filter(
        type__type="preschool_education_fi"
    ).exists()

    call_command("update_helsinki_preschool_districts")

    assert (
        AdministrativeDivision.objects.filter(
            type__type="preschool_education_fi"
        ).count()
        == 2
    )
    division_1 = AdministrativeDivision.objects.get(origin_id="333")
    assert division_1.name_fi == "Testialue"
    assert division_1.name_sv == "Testområde"
    assert division_1.type.type == "preschool_education_fi"
    assert division_1.municipality == municipality
    assert division_1.parent == municipality.division
    assert (
        division_1.ocd_id
        == "ocd-division/country:fi/kunta:helsinki/esiopetuksen_oppilaaksiottoalue_fi:333"
    )
    assert division_1.units == [14]
    assert division_1.extra == {"schoolyear": "2023-2024"}
    assert type(division_1.geometry.boundary) is MultiPolygon

    division_2 = AdministrativeDivision.objects.get(origin_id="444")
    assert division_2.name_fi == "Testialue"
    assert division_2.name_sv == "Testområde"
    assert division_2.type.type == "preschool_education_fi"
    assert division_2.municipality == municipality
    assert division_2.parent == municipality.division
    assert (
        division_2.ocd_id
        == "ocd-division/country:fi/kunta:helsinki/esiopetuksen_oppilaaksiottoalue_fi:444"
    )
    assert division_2.units == [14]
    assert division_2.extra == {"schoolyear": "2024-2025"}
    assert type(division_2.geometry.boundary) is MultiPolygon


@pytest.mark.django_db
@patch(
    "services.management.commands.update_helsinki_preschool_districts.PRESCHOOL_DISTRICT_DATA",
    [
        {
            "source_type": "avoindata:Esiopetusalue_suomi",
            "division_type": "preschool_education_fi",
            "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
        },
        {
            "source_type": "avoindata:Esiopetusalue_suomi_tuleva",
            "division_type": "preschool_education_fi",
            "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
        },
    ],
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.school_district_importer.datetime"
)
def test_update_preschool_districts_removes_school_year(
    mock_datetime, get_feature_mock, municipality
):
    """
    When date is between 1.8. and 15.12. the previous preschool year should be removed
    """
    mock_datetime.today.return_value = datetime(2024, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    call_command("update_helsinki_preschool_districts")

    assert (
        AdministrativeDivision.objects.filter(
            type__type="preschool_education_fi"
        ).count()
        == 1
    )
    assert AdministrativeDivision.objects.filter(extra__schoolyear="2024-2025").exists()


@pytest.mark.django_db
@patch(
    "services.management.commands.update_helsinki_preschool_districts.PRESCHOOL_DISTRICT_DATA",
    [
        {
            "source_type": "avoindata:Esiopetusalue_suomi_broken",
            "division_type": "preschool_education_fi",
            "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
        },
    ],
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.school_district_importer.datetime"
)
def test_update_preschool_districts_with_broken_data(
    mock_datetime, get_feature_mock, municipality, caplog
):
    """
    If source data has broken features, it should skip them and import everything it
    can while logging the errors.
    """
    mock_datetime.today.return_value = datetime(2023, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)
    caplog.clear()

    call_command("update_helsinki_preschool_districts")

    assert any(
        record.levelname == "ERROR" and "Failed to import division" in record.msg
        for record in caplog.records
    )
    assert any(
        record.levelname == "WARNING"
        and "Finished importing districts with errors" in record.msg
        for record in caplog.records
    )

    assert (
        AdministrativeDivision.objects.filter(
            type__type="preschool_education_fi"
        ).count()
        == 1
    )
    assert AdministrativeDivision.objects.filter(extra__schoolyear="2023-2024").exists()


@pytest.mark.django_db
@patch(
    "services.management.commands.update_helsinki_preschool_districts.PRESCHOOL_DISTRICT_DATA",
    [
        {
            "source_type": "avoindata:Esiopetusalue_suomi_no_unit",
            "division_type": "preschool_education_fi",
            "ocd_id": "esiopetuksen_oppilaaksiottoalue_fi",
        },
    ],
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.school_district_importer.datetime"
)
def test_should_update_preschool_districts_without_units(
    mock_datetime, get_feature_mock, municipality
):
    """
    Should create pre-school districts even if they don't have any units.
    """
    mock_datetime.today.return_value = datetime(2023, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    call_command("update_helsinki_preschool_districts")

    assert (
        AdministrativeDivision.objects.filter(
            type__type="preschool_education_fi"
        ).count()
        == 1
    )
    division = AdministrativeDivision.objects.filter(
        type__type="preschool_education_fi"
    ).first()
    assert division.units == []
    assert division.extra.get("schoolyear") == "2023-2024"


@pytest.mark.django_db
@patch(
    "services.management.commands.update_helsinki_school_districts.SCHOOL_DISTRICT_DATA",
    [
        {
            "source_type": "avoindata:Opev_ooa_alaaste_suomi_no_unit",
            "division_type": "lower_comprehensive_school_district_fi",
            "ocd_id": "oppilaaksiottoalue_alakoulu",
        },
    ],
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
@patch(
    "services.management.commands.school_district_import.school_district_importer.datetime"
)
def test_should_update_school_districts_without_units(
    mock_datetime, get_feature_mock, municipality
):
    """
    Should create school districts even if they don't have any units.
    """
    mock_datetime.today.return_value = datetime(2023, 8, 1)
    mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    get_feature_mock.side_effect = lambda type_name: get_mock_data(type_name)

    call_command("update_helsinki_school_districts")

    assert (
        AdministrativeDivision.objects.filter(
            type__type="lower_comprehensive_school_district_fi"
        ).count()
        == 1
    )
    division = AdministrativeDivision.objects.filter(
        type__type="lower_comprehensive_school_district_fi"
    ).first()
    assert division.units == []
    assert division.start.year == 2023
    assert division.end.year == 2024


@pytest.mark.parametrize(
    "name",
    [
        "2023-2024",
        pytest.param("2023 - 2024", marks=pytest.mark.xfail),
        "Alakoulu 2023-2024",
        "Koskenjärviniemen yläkoulu 2023-2024",
        "Ali-Kosken yliopistollinen esikoulu 2023-2024",
        pytest.param(
            "Palsternakka-Cavoniuksen ala- ja yläasteen koulu 2023 - 2024",
            marks=pytest.mark.xfail,
        ),
    ],
)
def test_get_start_date_from_name(name):
    assert SchoolDistrictImporter.get_start_date_from_name(name) == "2023-08-01"


@pytest.mark.parametrize(
    "name",
    [
        "2023-2024",
        "2023 - 2024",
        "Alakoulu 2023-2024",
        "Koskenjärviniemen yläkoulu 2023-2024",
        "Ali-Kosken yliopistollinen esikoulu 2023-2024",
        "Palsternakka-Cavoniuksen ala- ja yläasteen koulu 2023 - 2024",
    ],
)
def test_get_end_date_from_name(name):
    assert SchoolDistrictImporter.get_end_date_from_name(name) == "2024-07-31"
