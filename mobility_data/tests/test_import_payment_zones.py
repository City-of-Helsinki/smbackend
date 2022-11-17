"""
Note, namespace declaration:
http://www.tekla.com/schemas/GIS
https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx
?SERVICE=WFS&REQUEST=DescribeFeatureType&typeName=GIS:Pysakoinnin_maksuvyohykkeet "
has been removed from the test input data, as it causes GDAL
DataSource to fail when loading data.
"""

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point, Polygon

from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_import_payment_zones():
    import_command("import_wfs", "PaymentZone", test_mode=True)
    assert ContentType.objects.all().count() == 1
    content_type = ContentType.objects.first()
    assert content_type.name == "PaymentZone"
    assert MobileUnit.objects.all().count() == 2
    payment_zone0 = MobileUnit.objects.all()[0]
    payment_zone1 = MobileUnit.objects.all()[1]

    payment_zone0.content_type == content_type
    payment_zone1.content_type == content_type
    market_square = Point(
        239760.23602773887, 6711049.638094525, srid=settings.DEFAULT_SRID
    )
    turku_cathedral = Point(
        245497.83040278094, 6710749.819904401, srid=settings.DEFAULT_SRID
    )
    forum_marinum = Point(
        237944.11102389736, 6709556.670906566, srid=settings.DEFAULT_SRID
    )

    assert payment_zone0.extra["maksuvyohykehinta"] == "3,0 €/h"
    assert payment_zone1.extra["maksuvyohykehinta"] == "1,5 €/h"
    assert payment_zone0.extra["maksullisuus_lauantai"] == "9-15"
    assert payment_zone1.extra["maksullisuus_lauantai"] == "9-15"

    assert payment_zone0.geometry.contains(market_square) is True
    assert payment_zone0.geometry.contains(turku_cathedral) is False
    assert payment_zone0.geometry.contains(forum_marinum) is False

    assert market_square.contains(payment_zone1.geometry) is False
    assert forum_marinum.contains(payment_zone1.geometry) is False

    assert isinstance(payment_zone0.geometry, Polygon)
