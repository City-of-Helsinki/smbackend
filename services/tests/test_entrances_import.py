import math
from datetime import UTC, datetime

import pytest

from services.management.commands.services_import.entrances import import_entrances
from services.models import Unit, UnitEntrance

from .utils import get_test_location, get_test_resource

ENTRANCE_SRC_SRID = 4326


def create_units():
    Unit.objects.create(id=23, last_modified_time=datetime.now(UTC))
    Unit.objects.create(id=8062, last_modified_time=datetime.now(UTC))


@pytest.mark.django_db
def test_entrances_import():
    def mock_pk_get(*_, **__):
        return get_test_resource(resource_name="entrances")

    create_units()

    import_entrances(mock_pk_get)

    unit_entrance_1_location = get_test_location(
        24.852525143795333, 60.2185902753135878, ENTRANCE_SRC_SRID
    )

    assert UnitEntrance.objects.count() == 6

    unit_1_entrances = UnitEntrance.objects.filter(unit__id=23)
    assert unit_1_entrances.count() == 3

    unit_2_entrances = UnitEntrance.objects.filter(unit__id=8062)
    assert unit_2_entrances.count() == 3

    unit_entrance = UnitEntrance.objects.get(pk=2801)
    assert unit_entrance.unit.id == 23
    assert unit_entrance.name_fi == "vaihtoehtoinen sisäänkäynti"
    assert unit_entrance.name_sv == "alternativ ingång"
    assert unit_entrance.name_en == "alternative entrance"
    assert not unit_entrance.is_main_entrance
    assert math.isclose(
        unit_entrance.location.x, unit_entrance_1_location.x, rel_tol=1e-6
    )
    assert math.isclose(
        unit_entrance.location.y, unit_entrance_1_location.y, rel_tol=1e-6
    )
