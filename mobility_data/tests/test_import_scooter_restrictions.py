from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point

from mobility_data.importers.wfs import DEFAULT_SOURCE_DATA_SRID, import_wfs_feature
from mobility_data.management.commands.import_wfs import CONFIG_FILE, get_yaml_config
from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_data_source

"""
Note, namespace declarations has been removed from the test input data, as it causes GDAL
DataSource to fail when loading data.
scooter_parkings.gml:
xsi:schemaLocation="http://www.opengis.net/wfs
http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd http://www.tekla.com/schemas/GIS
https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx
?SERVICE=WFS&REQUEST=DescribeFeatureType&typeName=GIS:Sahkopotkulautaparkki "
scooter_speed_limits.gml:
xsi:schemaLocation="http://www.opengis.net/wfs
http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd
http://www.tekla.com/schemas/GIS
https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx
?SERVICE=WFS&REQUEST=DescribeFeatureType&typeName=GIS:Sahkopotkulauta_nopeusrajoitus "
scooter_no_parking_zones.gml:
xsi:schemaLocation="http://www.opengis.net/wfs
http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd
http://www.tekla.com/schemas/GIS
https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx
?SERVICE=WFS&REQUEST=DescribeFeatureType&typeName=GIS:Sahkopotkulauta_pysakointikielto "
"""


@pytest.mark.django_db
@patch("mobility_data.importers.wfs.get_data_source")
def test_import_scooter_restrictions(get_data_source_mock):
    config = get_yaml_config(CONFIG_FILE)
    get_data_source_mock.return_value = get_test_fixture_data_source(
        "scooter_parkings.gml"
    )
    features = ["ScooterParkingArea"]
    for feature in config["features"]:
        if feature["content_type_name"] in features:
            import_wfs_feature(feature)
    # Test scooter parking
    parking_content_type = ContentType.objects.get(type_name="ScooterParkingArea")
    assert parking_content_type
    parking_units_qs = MobileUnit.objects.filter(content_types=parking_content_type)
    assert parking_units_qs.count() == 3
    parking_unit = parking_units_qs[2]
    assert parking_unit.content_types.all().count() == 1
    parking_unit.content_types.first() == parking_content_type
    point = Point(239576.42, 6711050.26, srid=DEFAULT_SOURCE_DATA_SRID)
    parking_unit.geometry.equals_exact(point, tolerance=0.0001)
    get_data_source_mock.return_value = get_test_fixture_data_source(
        "scooter_speed_limits.gml"
    )
    features = ["ScooterSpeedLimitArea"]
    for feature in config["features"]:
        if feature["content_type_name"] in features:
            import_wfs_feature(feature)
    # Test scooter speed limits
    speed_limit_content_type = ContentType.objects.get(
        type_name="ScooterSpeedLimitArea"
    )
    assert speed_limit_content_type
    speed_limits_qs = MobileUnit.objects.filter(content_types=speed_limit_content_type)
    assert speed_limits_qs.count() == 3
    speed_limit_unit = MobileUnit.objects.get(id=speed_limits_qs[0].id)
    assert speed_limit_unit.content_types.all().count() == 1
    assert speed_limit_unit.content_types.first() == speed_limit_content_type
    market_square = Point(239755.11, 6711065.07, srid=settings.DEFAULT_SRID)
    turku_cathedral = Point(240377.95, 6711025.00, srid=settings.DEFAULT_SRID)
    # Scooter speed limit unit locates in the market square(kauppator)
    assert speed_limit_unit.geometry.contains(market_square) is True
    assert speed_limit_unit.geometry.contains(turku_cathedral) is False
    get_data_source_mock.return_value = get_test_fixture_data_source(
        "scooter_no_parking_zones.gml"
    )
    features = ["ScooterNoParkingArea"]
    for feature in config["features"]:
        if feature["content_type_name"] in features:
            import_wfs_feature(feature)
    # Test scooter no parking zones
    no_parking_content_type = ContentType.objects.get(type_name="ScooterNoParkingArea")
    assert no_parking_content_type
    no_parking_qs = MobileUnit.objects.filter(content_types=no_parking_content_type)
    assert no_parking_qs.count() == 3
    no_parking_unit = MobileUnit.objects.get(id=no_parking_qs[0].id)
    assert no_parking_unit.content_types.all().count() == 1
    assert no_parking_unit.content_types.first() == no_parking_content_type
    aninkaisten_bridge = Point(239808.23, 6711973.03, srid=settings.DEFAULT_SRID)
    # no_parking_unit locates in aninkaisten bridge
    assert no_parking_unit.geometry.contains(aninkaisten_bridge) is True
    assert no_parking_unit.geometry.contains(market_square) is False
