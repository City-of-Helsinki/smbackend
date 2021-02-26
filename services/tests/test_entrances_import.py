import math
from datetime import datetime
from unittest.mock import patch

import pytest
import pytz

from services.models import Unit, UnitEntrance

from .utils import get_test_location, get_test_resource

ENTRANCE_SRC_SRID = 4326


def create_units():
    utc_timezone = pytz.timezone("UTC")
    Unit.objects.create(id=23, last_modified_time=datetime.now(utc_timezone))
    Unit.objects.create(id=8062, last_modified_time=datetime.now(utc_timezone))


@pytest.mark.django_db
@patch("services.management.commands.services_import_v4.Command.pk_get")
def test_entrances_import(entrance_resource):
    from services.management.commands.services_import_v4 import import_entrances

    create_units()

    entrance_resource.return_value = get_test_resource(resource_name="entrances")

    import_entrances()

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
