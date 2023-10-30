from datetime import datetime
from unittest.mock import patch

import pytest
import pytz
from django.core.management import call_command

from services.models import Unit, UnitIdentifier


def get_mock_data():
    """
    Return mock data for the MiniWFS get_feature method.
    """
    return "services/tests/data/melontareitti_3d.gml"


@pytest.mark.django_db
@patch("services.management.commands.lipas_import.MiniWFS.get_feature")
def test_lipas_import_3d(get_feature_mock):
    """
    Test that the lipas_import_3d command imports 3D geometries correctly to the right unit.
    """
    get_feature_mock.return_value = get_mock_data()

    unit = Unit.objects.create(
        id=1, last_modified_time=datetime.now(pytz.utc), name_fi="Melontareitti"
    )
    unit_without_geometry_3d = Unit.objects.create(
        id=2, last_modified_time=datetime.now(pytz.utc), name_fi="Kuntopolku"
    )
    UnitIdentifier.objects.create(unit_id=unit.id, namespace="lipas", value="601110")

    assert unit.geometry_3d is None
    assert unit_without_geometry_3d.geometry_3d is None

    call_command("lipas_import_3d", muni_id="92")
    unit.refresh_from_db()
    unit_without_geometry_3d.refresh_from_db()

    assert unit.geometry_3d is not None
    assert unit_without_geometry_3d.geometry_3d is None

    assert unit.geometry_3d.geom_type == "MultiLineString"
    assert "Z" in unit.geometry_3d.ewkt  # Test that is 3D
