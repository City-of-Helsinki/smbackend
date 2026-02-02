from unittest.mock import MagicMock, patch

import pytest
from django.contrib.gis.geos import LineString, MultiLineString, MultiPolygon, Polygon
from django.core.management import call_command
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

from services.management.commands.update_vantaa_parking_areas import (
    Command,
    UnsupportedGeometryError,
)


@pytest.fixture
def mock_parking_areas_data():
    """Fixture for standard parking areas with mixed geometry types."""
    return [
        {
            "geometry": {
                "coordinates": [
                    [
                        [25.084374753255055, 60.3499294370369],
                        [25.08408380151095, 60.34990982397221],
                        [25.084089858850913, 60.34983805624883],
                        [25.084383300724973, 60.349855193165794],
                        [25.084374753255055, 60.3499294370369],
                    ]
                ],
                "type": "Polygon",
            },
            "id": 1,
            "properties": {
                "aikarajoitus": "30 min",
                "aikarajoitus_num": None,
                "aluetunnus": None,
                "katu": None,
                "kaupunginosa": None,
                "kiekkopaikka": "Kyllä",
                "lisätiedot": None,
                "objectid": 1,
                "objectid_1": None,
                "paikkamäärä": 6,
                "paikkamääräap": "6 ap",
                "tyyppi": "Lyhytaikainen",
                "voimassaoloaika": None,
            },
            "type": "Feature",
        },
        {
            "geometry": {
                "coordinates": [
                    [25.049797811943435, 60.35260110313705],
                    [25.049934474444232, 60.35248545784165],
                    [25.05008239193723, 60.35239648422703],
                    [25.050167558514346, 60.35234643499014],
                    [25.05058901570631, 60.352171773300924],
                ],
                "type": "LineString",
            },
            "id": 2,
            "properties": {
                "aikarajoitus": None,
                "aikarajoitus_num": None,
                "aluetunnus": None,
                "katu": None,
                "kaupunginosa": None,
                "kiekkopaikka": "Ei",
                "lisätiedot": None,
                "objectid": 2,
                "objectid_1": 2,
                "paikkamäärä": 8,
                "paikkamääräap": "8 ap",
                "tyyppi": "Ei rajoitusta",
                "voimassaoloaika": None,
            },
            "type": "Feature",
        },
    ]


@pytest.fixture
def mock_parking_areas_null_geometry_data():
    """Fixture for parking areas with null geometry."""
    return [
        {
            "geometry": None,
            "id": 3,
            "properties": {
                "aikarajoitus": "30 min",
                "aikarajoitus_num": None,
                "aluetunnus": None,
                "katu": None,
                "kaupunginosa": None,
                "kiekkopaikka": "Kyllä",
                "lisätiedot": None,
                "objectid": 3,
                "objectid_1": None,
                "paikkamäärä": 6,
                "paikkamääräap": "6 ap",
                "tyyppi": "Lyhytaikainen",
                "voimassaoloaika": None,
            },
            "type": "Feature",
        }
    ]


@pytest.fixture
def mock_multilinestring_data():
    """Fixture for parking areas with MultiLineString geometry."""
    return [
        {
            "geometry": {
                "coordinates": [
                    [
                        [25.049797811943435, 60.35260110313705],
                        [25.049934474444232, 60.35248545784165],
                        [25.05008239193723, 60.35239648422703],
                    ],
                    [
                        [25.050167558514346, 60.35234643499014],
                        [25.05058901570631, 60.352171773300924],
                        [25.0508, 60.3520],
                    ],
                ],
                "type": "MultiLineString",
            },
            "id": 1,
            "properties": {
                "aikarajoitus": None,
                "aikarajoitus_num": None,
                "aluetunnus": None,
                "katu": "Test Street",
                "kaupunginosa": None,
                "kiekkopaikka": "Ei",
                "lisätiedot": None,
                "objectid": 1,
                "objectid_1": 1,
                "paikkamäärä": 15,
                "paikkamääräap": "15 ap",
                "tyyppi": "Ei rajoitusta",
                "voimassaoloaika": None,
            },
            "type": "Feature",
        }
    ]


def create_mock_query_result(features):
    """Helper function to create a mock query result from feature data.

    Returns the features list directly since the code uses len() and iteration.
    """
    return features


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
def test_update_parking_areas(mock_feature_service, mock_parking_areas_data):
    # Mock the FeatureService and its layer and features
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

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
def test_delete_removed_parking_areas(mock_feature_service, mock_parking_areas_data):
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

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
def test_skip_parking_areas_with_no_geometry(
    mock_feature_service, mock_parking_areas_null_geometry_data
):
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_null_geometry_data
    )

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    assert AdministrativeDivision.objects.count() == 0
    call_command("update_vantaa_parking_areas")
    assert AdministrativeDivision.objects.count() == 0


@pytest.mark.django_db
def test_transform_line_to_polygon():
    """Test transformation of LineString to Polygon with buffering."""
    command = Command()

    line = LineString((25.0, 60.0), (25.001, 60.001), srid=4326)

    result = command.transform_line_to_polygon(line)

    assert isinstance(result, (Polygon, MultiPolygon))
    assert result.srid == 4326
    assert result.area > 0


@pytest.mark.django_db
def test_get_multi_geom_polygon():
    """Test get_multi_geom with a Polygon."""
    command = Command()

    polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)), srid=4326)

    result = command.get_multi_geom(polygon)

    assert isinstance(result, MultiPolygon)
    assert result.srid == 4326
    assert len(result) == 1


@pytest.mark.django_db
def test_get_multi_geom_multipolygon():
    """Test get_multi_geom with a MultiPolygon (should return as-is)."""
    command = Command()

    multi_polygon = MultiPolygon(
        Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))),
        Polygon(((2, 2), (2, 3), (3, 3), (3, 2), (2, 2))),
        srid=4326,
    )

    result = command.get_multi_geom(multi_polygon)

    assert isinstance(result, MultiPolygon)
    assert result.srid == 4326
    assert len(result) == 2


@pytest.mark.django_db
def test_get_multi_geom_linestring():
    """Test get_multi_geom with a LineString (should buffer to MultiPolygon)."""
    command = Command()

    line = LineString((25.0, 60.0), (25.001, 60.001), srid=4326)

    result = command.get_multi_geom(line)

    assert isinstance(result, MultiPolygon)
    assert result.srid == 4326
    assert result.area > 0


@pytest.mark.django_db
def test_get_multi_geom_multilinestring():
    """Test get_multi_geom with a MultiLineString (should buffer to MultiPolygon)."""
    command = Command()

    multi_line = MultiLineString(
        LineString((25.0, 60.0), (25.001, 60.001)),
        LineString((25.002, 60.002), (25.003, 60.003)),
        srid=4326,
    )

    result = command.get_multi_geom(multi_line)

    assert isinstance(result, MultiPolygon)
    assert result.srid == 4326
    assert result.area > 0


@pytest.mark.django_db
def test_get_multi_geom_unsupported():
    """Test get_multi_geom with unsupported geometry type."""
    from django.contrib.gis.geos import Point

    command = Command()

    point = Point(25.0, 60.0, srid=4326)

    with pytest.raises(UnsupportedGeometryError) as exc_info:
        command.get_multi_geom(point)

    assert "Unsupported geometry type: Point" in str(exc_info.value)


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
def test_pagination_with_object_ids(mock_feature_service):
    """Test pagination using object IDs when more than batch size features exist."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value

    mock_oids_result = MagicMock()
    mock_oids_result.objectIds = [1, 2, 3, 4, 5]

    def mock_query(**kwargs):
        if kwargs.get("returnIdsOnly"):
            return mock_oids_result
        elif "objectIds" in kwargs:
            oid_string = kwargs["objectIds"]
            oids = [int(oid) for oid in oid_string.split(",")]
            features = []
            for oid in oids:
                features.append(
                    {
                        "geometry": {
                            "coordinates": [
                                [
                                    [25.0, 60.0],
                                    [25.001, 60.0],
                                    [25.001, 60.001],
                                    [25.0, 60.001],
                                    [25.0, 60.0],
                                ]
                            ],
                            "type": "Polygon",
                        },
                        "id": oid,
                        "properties": {"objectid": oid, "tyyppi": "Lyhytaikainen"},
                        "type": "Feature",
                    }
                )

            mock_result = MagicMock()
            mock_result.count = len(features)
            mock_result.__iter__ = lambda self: iter(features)
            return mock_result
        else:
            return MagicMock()

    mock_layer_instance.query.side_effect = mock_query

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    assert AdministrativeDivision.objects.count() == 5


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
def test_pagination_fallback_no_object_ids(
    mock_feature_service, mock_parking_areas_data
):
    """Test fallback when object IDs cannot be retrieved."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value

    def mock_query(**kwargs):
        if kwargs.get("returnIdsOnly"):
            return {}
        else:
            return create_mock_query_result(mock_parking_areas_data)

    mock_layer_instance.query.side_effect = mock_query

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    assert AdministrativeDivision.objects.count() == 2


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
def test_translations_applied(mock_feature_service, mock_parking_areas_data):
    """Test that name translations are applied correctly."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    obj = AdministrativeDivision.objects.get(origin_id=1)

    assert obj.name_fi == "Lyhytaikainen"
    assert obj.name_en == "Temporary"
    assert obj.name_sv == "Kortvarig"


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
def test_skip_parking_areas_without_origin_id(mock_feature_service):
    """Test that parking areas without origin_id are skipped."""
    mock_data = MagicMock()
    mock_data.count = 1
    mock_data.__iter__ = lambda self: iter(
        [
            {
                "geometry": {
                    "coordinates": [
                        [
                            [25.0, 60.0],
                            [25.001, 60.0],
                            [25.001, 60.001],
                            [25.0, 60.001],
                            [25.0, 60.0],
                        ]
                    ],
                    "type": "Polygon",
                },
                "id": 1,
                "properties": {"objectid": None, "tyyppi": "Lyhytaikainen"},
                "type": "Feature",
            }
        ]
    )

    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = mock_data

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    assert AdministrativeDivision.objects.count() == 0


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_areas.DATA_SOURCES",
    [
        {
            "type": "street_parking_area",
            "service_url": "https://url",
            "layer_name": "Kadunvarsipysäköinti MUOKATTAVA",
            "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/kadunvarsipysakointi-alue:",
        }
    ],
)
@patch("restapi.FeatureService")
def test_multiple_data_source_types(mock_feature_service, mock_parking_areas_data):
    """Test handling of different data source types."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

    Municipality.objects.create(id="vantaa", name="Vantaa")

    call_command("update_vantaa_parking_areas")

    # Should create the division type automatically
    assert AdministrativeDivisionType.objects.filter(
        type="street_parking_area"
    ).exists()

    division_type = AdministrativeDivisionType.objects.get(type="street_parking_area")
    assert "Kadunvarsipysäköinti" in division_type.name


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
def test_extra_properties_stored(mock_feature_service, mock_parking_areas_data):
    """Test that extra properties from the source are stored."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    obj = AdministrativeDivision.objects.get(origin_id=1)

    assert obj.extra is not None
    assert obj.extra.get("aikarajoitus") == "30 min"
    assert obj.extra.get("paikkamäärä") == 6
    assert obj.extra.get("kiekkopaikka") == "Kyllä"


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
def test_geometry_stored_correctly(mock_feature_service, mock_parking_areas_data):
    """Test that geometry is stored in AdministrativeDivisionGeometry."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    obj = AdministrativeDivision.objects.get(origin_id=1)

    geom = AdministrativeDivisionGeometry.objects.get(division=obj)
    assert geom.boundary is not None
    assert isinstance(geom.boundary, MultiPolygon)


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
def test_update_existing_parking_area(mock_feature_service, mock_parking_areas_data):
    """Test that existing parking areas are updated, not duplicated."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

    municipality = Municipality.objects.create(id="vantaa", name="Vantaa")
    division_type = AdministrativeDivisionType.objects.create(type="parking_area")

    # Create an existing parking area with old data
    ocd_id = "ocd-division/country:fi/kunta:vantaa/pysakointipaikka-alue:1"
    existing_div = AdministrativeDivision.objects.create(
        ocd_id=ocd_id,
        name_fi="Old Name",
        municipality=municipality,
        type=division_type,
        origin_id="1",
    )

    call_command("update_vantaa_parking_areas")

    # Should still have 2 objects (not 3)
    assert AdministrativeDivision.objects.count() == 2

    # The existing object should be updated
    updated_div = AdministrativeDivision.objects.get(pk=existing_div.pk)
    assert updated_div.name_fi == "Lyhytaikainen"
    assert updated_div.name_en == "Temporary"


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
def test_ocd_id_format(mock_feature_service, mock_parking_areas_data):
    """Test that OCD IDs are formatted correctly."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_parking_areas_data
    )

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="parking_area")

    call_command("update_vantaa_parking_areas")

    obj = AdministrativeDivision.objects.get(origin_id=1)

    expected_ocd_id = "ocd-division/country:fi/kunta:vantaa/pysakointipaikka-alue:1"
    assert obj.ocd_id == expected_ocd_id


@pytest.mark.django_db
@patch(
    "services.management.commands.update_vantaa_parking_areas.DATA_SOURCES",
    [
        {
            "type": "hgv_street_parking_area",
            "service_url": "https://url",
            "layer_name": "Raskaan liikenteen sallitut kadunvarret MUOKATTAVA",
            "ocd_id_base": "ocd-division/country:fi/kunta:vantaa/raskaanliikenteen-sallittu-kadunvarsi-alue:",
        }
    ],
)
@patch("restapi.FeatureService")
def test_multilinestring_geometry_handling(
    mock_feature_service, mock_multilinestring_data
):
    """Test handling of MultiLineString geometries (should buffer to MultiPolygon)."""
    mock_layer_instance = mock_feature_service.return_value.layer.return_value
    mock_layer_instance.query.return_value = create_mock_query_result(
        mock_multilinestring_data
    )

    Municipality.objects.create(id="vantaa", name="Vantaa")
    AdministrativeDivisionType.objects.create(type="hgv_street_parking_area")

    call_command("update_vantaa_parking_areas")

    assert AdministrativeDivision.objects.count() == 1

    obj = AdministrativeDivision.objects.get(origin_id=1)

    assert type(obj.geometry.boundary) is MultiPolygon
    assert obj.geometry.boundary.area > 0


@pytest.mark.django_db
def test_multipolygon_constructor_rejects_multipolygon():
    """Test that Django GEOS MultiPolygon constructor rejects MultiPolygon instances."""
    poly = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
    multi_poly = MultiPolygon(poly)

    with pytest.raises(TypeError):
        MultiPolygon([multi_poly])
