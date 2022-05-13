"""
Note, namespace declaration:
xsi:schemaLocation="http://www.opengis.net/wfs
http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd
http://www.tekla.com/schemas/GIS
https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx?SERVICE=WFS&REQUEST=DescribeFeatureType&typeName=GIS:Varusteet "
has been removed from the test input data, as it causes GDAL
DataSource to fail when loading data.
"""
import pytest
from django.conf import settings
from django.contrib.gis.geos import Point

from mobility_data.importers.accessories import SOURCE_DATA_SRID
from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_import_accessories(
    administrative_division,
    administrative_division_type,
    administrative_division_geometry,
):
    import_command("import_accessories", test_mode="accessories.gml")

    public_toilet_content_type = ContentType.objects.get(
        type_name=ContentType.ACCESSORY_PUBLIC_TOILET
    )
    assert public_toilet_content_type
    public_toilet_units_qs = MobileUnit.objects.filter(
        content_type=public_toilet_content_type
    )
    assert public_toilet_units_qs.count() == 2
    public_toilet_unit = public_toilet_units_qs[0]
    assert public_toilet_unit.content_type == public_toilet_content_type
    extra = public_toilet_unit.extra
    assert extra["Kunto"] == "Ei tietoa"
    assert extra["Malli"] == "Testi Vessa"
    assert extra["Pituus"] == 4.2
    assert extra["Asennus"] == "Paikalla"
    assert extra["Pinta-ala"] == "10"
    assert extra["Valmistaja"] == "Testi valmistaja"
    assert extra["Kunto_koodi"] == 24
    assert extra["Malli_koodi"] == 4242
    assert extra["Varustelaji"] == "WC"
    assert extra["Asennus_koodi"] == 42
    assert extra["Hankintavuosi"] == 1942
    assert extra["Valmistaja_koodi"] == 0
    assert extra["Varustelaji_koodi"] == 4022

    bench_content_type = ContentType.objects.get(type_name=ContentType.ACCESSORY_BENCH)
    assert bench_content_type

    bench_units_qs = MobileUnit.objects.filter(content_type=bench_content_type)
    # Bench id 107620803 locates in Kaarina and therefore is not included.
    assert bench_units_qs.count() == 1
    bench_unit = bench_units_qs.first()
    assert bench_unit.content_type == bench_content_type
    point = Point(23464051.217, 6706051.818, srid=SOURCE_DATA_SRID)
    point.transform(settings.DEFAULT_SRID)
    bench_unit.geometry.equals_exact(point, tolerance=0.0001)
    table_content_type = ContentType.objects.get(type_name=ContentType.ACCESSORY_TABLE)
    assert table_content_type
    table_units_qs = MobileUnit.objects.filter(content_type=table_content_type)
    assert table_units_qs.count() == 2
    assert table_units_qs[0].content_type == table_content_type

    furniture_group_content_type = ContentType.objects.get(
        type_name=ContentType.ACCESSORY_FURNITURE_GROUP
    )
    assert furniture_group_content_type
    furniture_group_units_qs = MobileUnit.objects.filter(
        content_type=furniture_group_content_type
    )
    assert furniture_group_units_qs.count() == 2
    assert furniture_group_units_qs[0].content_type == furniture_group_content_type
