import pytest
from django.contrib.gis.geos import Point
from munigeo.utils import get_default_srid

from mobility_data.importers.utils import get_closest_address


@pytest.mark.django_db
def test_get_closest_address(address):
    # Slightly offset from the "Test Street 42" address.
    point = Point(22.2441, 60.4001, srid=4326)
    point.transform(get_default_srid())
    assert get_closest_address(point).full_name_fi == "Test Street 42"


@pytest.mark.django_db
def test_get_closest_address_other_srid(address):
    # A point in a different SRID than Address.location is transformed.
    point = Point(22.2441, 60.4001, srid=4326)
    assert get_closest_address(point).full_name_fi == "Test Street 42"


@pytest.mark.django_db
def test_get_closest_address_no_srid(address):
    # A point without an SRID is assumed to be in the default SRID.
    point = Point(22.2441, 60.4001, srid=4326)
    point.transform(get_default_srid())
    point = Point(point.x, point.y)
    assert point.srid is None
    assert get_closest_address(point).full_name_fi == "Test Street 42"
