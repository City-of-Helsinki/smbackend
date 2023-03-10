from unittest.mock import patch

import pytest
from django.contrib.gis.geos import Point

from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_json_data


@pytest.mark.django_db
@patch("mobility_data.importers.utils.fetch_json")
def test_import_foli_stops(fetch_json_mock):
    from mobility_data.importers import foli_stops

    fetch_json_mock.return_value = get_test_fixture_json_data("foli_stops.json")
    objects = foli_stops.get_foli_stops()
    foli_stops.save_to_database(objects)
    assert ContentType.objects.count() == 1
    assert ContentType.objects.first().type_name == foli_stops.CONTENT_TYPE_NAME
    assert MobileUnit.objects.count() == 3
    turun_satama = MobileUnit.objects.get(name="Turun satama (Silja)")
    assert turun_satama.content_types.all().count() == 1
    assert turun_satama.content_types.first() == ContentType.objects.first()
    assert turun_satama.extra["stop_code"] == "1"
    assert turun_satama.extra["wheelchair_boarding"] == 0
    point_turun_satama = turun_satama.geometry
    point_turun_satama.transform(4326)
    assert point_turun_satama == Point(22.21966, 60.43497, srid=4326)
