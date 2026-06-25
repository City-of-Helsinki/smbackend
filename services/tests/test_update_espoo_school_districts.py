from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.gis.geos import MultiPolygon
from django.core.management import call_command
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)

from services.management.commands.school_district_import.base_school_district_importer import (  # noqa: E501
    BaseSchoolDistrictImporter,
)
from services.management.commands.school_district_import.espoo_school_district_importer import (  # noqa: E501
    EspooSchoolDistrictImporter,
)

FI_SOURCE = "GIS:Oppilaaksiottoalueet_suomenkielinen"
SV_SOURCE = "GIS:Oppilaaksiottoalueet_ruotsinkielinen_ala_aste"


class _SchoolDistrictImporter(BaseSchoolDistrictImporter):
    WFS_BASE = "https://example.com/wfs"


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


ESPOO_WFS_URL = "https://kartat.espoo.fi/teklaogcweb/wfs.ashx?request=GetFeature"


class _EspooFeature:
    def __init__(self, origin_id, name):
        self.origin_id = origin_id
        self.name = name

    def get(self, key):
        return {"Id": self.origin_id, "Nimi": self.name}.get(key)


def test_espoo_datasource_input_normalizes_legacy_epsg_3879_srs_name(requests_mock):
    requests_mock.get(
        ESPOO_WFS_URL,
        content=(
            b'<gml:Polygon srsName="'
            b"http://www.opengis.net/gml/srs/epsg.xml#3879"
            b'"></gml:Polygon>'
        ),
    )

    importer = EspooSchoolDistrictImporter(district_type="school")
    path, resource = importer.prepare_datasource_input(f"WFS:{ESPOO_WFS_URL}")

    try:
        assert Path(path).exists()
        content = Path(path).read_bytes()
        assert b"http://www.opengis.net/gml/srs/epsg.xml#3879" not in content
        assert b"EPSG:3879" in content
    finally:
        resource.cleanup()


@pytest.mark.parametrize(
    "url",
    [
        "WFS:http://kartat.espoo.fi/teklaogcweb/wfs.ashx?request=GetFeature",
        "WFS:https://example.com/wfs?request=GetFeature",
    ],
)
def test_espoo_datasource_input_rejects_unexpected_wfs_urls(requests_mock, url):
    importer = EspooSchoolDistrictImporter(district_type="school")

    with pytest.raises(ValueError, match="Unexpected Espoo WFS URL"):
        importer.prepare_datasource_input(url)

    assert not requests_mock.called


@pytest.mark.django_db
@patch.object(EspooSchoolDistrictImporter, "save_geometry")
@patch.object(EspooSchoolDistrictImporter, "fetch_layer")
@patch.object(EspooSchoolDistrictImporter, "get_school_year_start_years")
def test_espoo_import_districts_raises_after_attempting_all_divisions(
    get_years_mock,
    fetch_layer_mock,
    save_geometry_mock,
    municipality,
):
    importer = EspooSchoolDistrictImporter(district_type="school")
    features = [
        _EspooFeature("failed", "Failed district"),
        _EspooFeature("ok", "Successful district"),
    ]
    get_years_mock.return_value = [2026, 2027]
    fetch_layer_mock.return_value = features

    def save_geometry(feature, division):
        if division.origin_id == "failed_2026":
            raise RuntimeError("geometry failed")

    save_geometry_mock.side_effect = save_geometry

    with pytest.raises(
        RuntimeError, match="Failed to import one or more Espoo school districts"
    ):
        importer.import_districts(
            {
                "source_type": FI_SOURCE,
                "division_type": "lower_comprehensive_school_district_fi",
                "ocd_id": "oppilaaksiottoalue_alakoulu_fi",
            }
        )

    assert save_geometry_mock.call_count == 4
    assert not AdministrativeDivision.objects.filter(origin_id="failed_2026").exists()
    assert AdministrativeDivision.objects.filter(origin_id="ok_2026").exists()
    assert AdministrativeDivision.objects.filter(origin_id="ok_2027").exists()


@patch(
    "services.management.commands.school_district_import.base_school_district_importer.DataSource"
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
def test_fetch_layer_cleans_datasource_resource_on_open_failure(
    get_feature_mock, datasource_mock
):
    resource = Mock()
    importer = _SchoolDistrictImporter()
    importer.prepare_datasource_input = Mock(return_value=("features.gml", resource))
    get_feature_mock.return_value = "WFS:https://example.com/wfs?request=GetFeature"
    datasource_mock.side_effect = RuntimeError("open failed")

    with pytest.raises(RuntimeError, match="open failed"):
        importer.fetch_layer("test:layer")

    resource.cleanup.assert_called_once_with()


@patch(
    "services.management.commands.school_district_import.base_school_district_importer.DataSource"
)
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
def test_fetch_layer_keeps_datasource_resource_on_success(
    get_feature_mock, datasource_mock
):
    layer = MagicMock()
    layer.__len__.return_value = 0
    resource = Mock()
    importer = _SchoolDistrictImporter()
    importer.prepare_datasource_input = Mock(return_value=("features.gml", resource))
    get_feature_mock.return_value = "WFS:https://example.com/wfs?request=GetFeature"
    datasource_mock.return_value = [layer]

    assert importer.fetch_layer("test:layer") == layer
    assert layer._datasource_resource == resource
    resource.cleanup.assert_not_called()


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
@patch(
    "services.management.commands.update_espoo_school_districts."
    "EspooSchoolDistrictImporter.import_districts"
)
def test_update_espoo_school_districts_raises_on_layer_refresh_failure(
    import_districts_mock, municipality
):
    district_type = AdministrativeDivisionType.objects.create(
        type="lower_comprehensive_school_district_fi"
    )
    stale_division = AdministrativeDivision.objects.create(
        type=district_type,
        origin_id="stale",
        name="Stale district",
        municipality=municipality,
    )
    import_districts_mock.side_effect = RuntimeError("layer refresh failed")

    with pytest.raises(RuntimeError, match="layer refresh failed"):
        call_command("update_espoo_school_districts")

    assert AdministrativeDivision.objects.filter(pk=stale_division.pk).exists()


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
