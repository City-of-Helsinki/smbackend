"""
Note, namespace declaration:
xsi:schemaLocation="http://www.opengis.net/wfs
http://schemas.opengis.net/wfs/1.0.0/WFS-basic.xsd
http://www.tekla.com/schemas/GIS
https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx
?SERVICE=WFS&REQUEST=DescribeFeatureType&typeName=GIS:Nopeusrajoitusalueet "
has been removed from the test input data, as it causes GDAL
DataSource to fail when loading data.
"""
import pytest

from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_import_speed_limits():
    import_command("import_wfs", "SpeedLimitZone", test_mode=True)

    assert ContentType.objects.all().count() == 1
    content_type = ContentType.objects.first()
    assert content_type.name == "SpeedLimitZone"
    assert MobileUnit.objects.all().count() == 3

    zone_80 = MobileUnit.objects.all()[0]
    zone_40 = MobileUnit.objects.all()[1]
    zone_20 = MobileUnit.objects.all()[2]
    assert zone_80.content_type == content_type
    assert zone_40.content_type == content_type
    assert zone_20.content_type == content_type

    assert zone_80.extra["speed_limit"] == 80
    assert zone_40.extra["speed_limit"] == 40
    assert zone_20.extra["speed_limit"] == 20
