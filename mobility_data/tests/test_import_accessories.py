"""
Note, namespace declaration:
xsi:schemaLocation="http://www.opengis.net/wfs
http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd
http://www.tekla.com/schemas/GIS
https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx?SERVICE=WFS&REQUEST=DescribeFeatureType&typeName=GIS:Varusteet "
has been removed from the test input data, as it causes GDAL
DataSource to fail when loading data.
"""

from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point

from mobility_data.importers.wfs import DEFAULT_SOURCE_DATA_SRID, import_wfs_feature
from mobility_data.management.commands.import_wfs import CONFIG_FILE, get_yaml_config
from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_data_source


@pytest.mark.django_db
@patch("mobility_data.importers.wfs.get_data_source")
def test_import_accessories(
    get_data_source_mock,
    administrative_division,
    administrative_division_type,
    administrative_division_geometry,
):
    config = get_yaml_config(CONFIG_FILE)
    get_data_source_mock.return_value = get_test_fixture_data_source("accessories.gml")
    features = ["PublicToilet", "PublicTable", "PublicBench", "PublicFurnitureGroup"]
    for feature in config["features"]:
        if feature["content_type_name"] in features:
            import_wfs_feature(feature)
    public_toilet_content_type = ContentType.objects.get(type_name="PublicToilet")
    public_toilet_units_qs = MobileUnit.objects.filter(
        content_types=public_toilet_content_type
    )
    assert public_toilet_units_qs.count() == 2
    public_toilet_unit = public_toilet_units_qs[0]
    assert public_toilet_unit.content_types.all().count() == 1
    assert public_toilet_unit.content_types.first() == public_toilet_content_type
    extra = public_toilet_unit.extra
    assert extra["Kunto"] == "Ei tietoa"
    assert extra["Malli"] == "Testi Vessa"
    assert extra["Pituus"] == 4.2
    assert extra["Asennus"] == "Paikalla"
    assert extra["Valmistaja"] == "Testi valmistaja"
    assert extra["Kunto_koodi"] == 24
    assert extra["Malli_koodi"] == 4242
    assert extra["Varustelaji"] == "WC"
    assert extra["Asennus_koodi"] == 42
    assert extra["Hankintavuosi"] == 1942
    assert extra["Valmistaja_koodi"] == 0
    assert extra["Varustelaji_koodi"] == 4022

    bench_content_type = ContentType.objects.get(type_name="PublicBench")
    bench_units_qs = MobileUnit.objects.filter(content_types=bench_content_type)
    # Bench id 107620803 locates in Kaarina and therefore is not included.
    assert bench_units_qs.count() == 1
    bench_unit = bench_units_qs.first()
    assert bench_unit.content_types.all().count() == 1
    assert bench_unit.content_types.first() == bench_content_type
    point = Point(23464051.217, 6706051.818, srid=DEFAULT_SOURCE_DATA_SRID)
    point.transform(settings.DEFAULT_SRID)
    bench_unit.geometry.equals_exact(point, tolerance=0.0001)

    table_content_type = ContentType.objects.get(type_name="PublicTable")
    table_units_qs = MobileUnit.objects.filter(content_types=table_content_type)
    assert table_units_qs.count() == 2
    assert table_units_qs[0].content_types.all().count() == 1
    assert table_units_qs[0].content_types.first() == table_content_type

    furniture_group_content_type = ContentType.objects.get(
        type_name="PublicFurnitureGroup"
    )
    furniture_group_units_qs = MobileUnit.objects.filter(
        content_types=furniture_group_content_type
    )
    assert furniture_group_units_qs.count() == 2
    assert furniture_group_units_qs[0].content_types.all().count() == 1
    assert (
        furniture_group_units_qs[0].content_types.first()
        == furniture_group_content_type
    )
