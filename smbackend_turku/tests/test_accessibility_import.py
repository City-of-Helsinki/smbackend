import logging
from datetime import datetime
from unittest.mock import patch

import pytest
import pytz

from services.models import (
    AccessibilityVariable,
    Unit,
    UnitAccessibilityProperty,
    UnitIdentifier,
)
from smbackend_turku.tests.test_units_import import (
    create_municipality,
    get_test_resource,
)


def create_units():
    utc_timezone = pytz.timezone("UTC")
    unit_1 = Unit.objects.create(id=740, last_modified_time=datetime.now(utc_timezone))
    unit_2 = Unit.objects.create(id=967, last_modified_time=datetime.now(utc_timezone))
    ptv_id_1 = "8j76h2hj-hb8b-8j87-j7g7-8796hg87654k"
    ptv_id_2 = "hs8790h7-h898-97h7-s9kj-86597867g978"
    UnitIdentifier.objects.create(namespace="ptv", value=ptv_id_1, unit=unit_1)
    UnitIdentifier.objects.create(namespace="ptv", value=ptv_id_2, unit=unit_2)


@pytest.mark.django_db
@patch("smbackend_turku.importers.utils.get_ar_servicepoint_accessibility_resource")
@patch("smbackend_turku.importers.utils.get_ar_servicepoint_resource")
@patch("smbackend_turku.importers.utils.get_ar_resource")
def test_accessibility_variables_import(
    ar_resource, ar_se_resource, ar_se_accessibility_resource
):
    from smbackend_turku.importers.accessibility import AccessibilityImporter

    logger = logging.getLogger(__name__)
    accessibility_importer = AccessibilityImporter(logger=logger)

    ar_resource.return_value = get_test_resource(
        resource_name="accessibility/variables"
    )
    ar_se_resource.return_value = get_test_resource(resource_name="info")
    ar_se_accessibility_resource.return_value = get_test_resource(
        resource_name="properties"
    )

    # Create Municipality needed for Units creation
    create_municipality()

    # Create Units needed for Accessibility Import
    create_units()

    accessibility_importer.import_accessibility()

    accessibility_objects = AccessibilityVariable.objects.all()
    accessibility_1 = AccessibilityVariable.objects.get(id=72)
    accessibility_2 = AccessibilityVariable.objects.get(id=259)

    assert len(accessibility_objects) == 5
    assert (
        accessibility_1.name
        == "ENTRANCE.DOOR.sufficiently_room_for_wheelchair_in_front"
    )
    assert accessibility_2.name == "INTERIOR.DOORS.stand_out_clearly"

    ptv_id_1 = "8j76h2hj-hb8b-8j87-j7g7-8796hg87654k"
    ptv_id_2 = "hs8790h7-h898-97h7-s9kj-86597867g978"

    unit_identifier_1 = UnitIdentifier.objects.get(namespace="ptv", value=ptv_id_1)
    unit_identifier_2 = UnitIdentifier.objects.get(namespace="ptv", value=ptv_id_2)

    unit_accessibility_properties = UnitAccessibilityProperty.objects.count()
    assert UnitAccessibilityProperty.objects.get(
        unit=unit_identifier_1.unit, variable_id=259
    )
    assert UnitAccessibilityProperty.objects.get(
        unit=unit_identifier_2.unit, variable_id=72
    )

    unit_accessibility_property_1 = UnitAccessibilityProperty.objects.get(
        unit=unit_identifier_1.unit, variable_id=259
    )
    unit_accessibility_property_2 = UnitAccessibilityProperty.objects.get(
        unit=unit_identifier_2.unit, variable_id=72
    )

    assert unit_accessibility_properties == 5
    assert unit_accessibility_property_1.value == "true"
    assert unit_accessibility_property_2.value == "false"
