from unittest.mock import patch

import pytest

from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit

from .utils import get_test_fixture_json_data


@pytest.mark.django_db
@patch("mobility_data.importers.under_and_overpasses.get_json_data")
def test_import_foli_stops(get_json_data_mock):
    from mobility_data.importers.under_and_overpasses import (
        get_under_and_overpass_objects,
        OVERPASS_CONTENT_TYPE_NAME,
        UNDERPASS_CONTENT_TYPE_NAME,
    )

    get_json_data_mock.return_value = get_test_fixture_json_data(
        "under_and_overpasses.json"
    )
    underpass_objects, overpass_objects = get_under_and_overpass_objects()
    assert len(underpass_objects) == 1
    assert len(overpass_objects) == 1
    underpass_content_type = get_or_create_content_type_from_config(
        UNDERPASS_CONTENT_TYPE_NAME
    )
    num_created, num_deleted = save_to_database(
        underpass_objects, underpass_content_type
    )
    assert num_created == 1
    assert num_deleted == 0
    assert (
        ContentType.objects.filter(type_name=UNDERPASS_CONTENT_TYPE_NAME).count() == 1
    )
    assert MobileUnit.objects.filter(content_types=underpass_content_type).count() == 1
    overpass_content_type = get_or_create_content_type_from_config(
        OVERPASS_CONTENT_TYPE_NAME
    )
    num_created, num_deleted = save_to_database(overpass_objects, overpass_content_type)
    assert num_created == 1
    assert num_deleted == 0
    assert ContentType.objects.filter(type_name=OVERPASS_CONTENT_TYPE_NAME).count() == 1
    assert MobileUnit.objects.filter(content_types=overpass_content_type).count() == 1

    assert MobileUnit.objects.count() == 2
    assert ContentType.objects.count() == 2
