from datetime import UTC, datetime

import pytest
from django.core.management import call_command

from services.models import Unit


@pytest.mark.django_db
def test_import_irregular_geometry():
    unit = Unit.objects.create(
        id=23795,
        name="Östersundomin koirametsä",
        last_modified_time=datetime.now(UTC),
    )
    assert unit.geometry is None

    call_command("import_irregular_geometry")
    unit.refresh_from_db()

    assert unit.geometry is not None
    assert unit.geometry.geom_type == "MultiPolygon"
    assert unit.geometry.area > 0
