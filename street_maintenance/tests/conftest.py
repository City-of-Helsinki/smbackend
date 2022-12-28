from datetime import datetime, timedelta

import pytest
import pytz
from django.contrib.gis.geos import LineString
from rest_framework.test import APIClient

from street_maintenance.management.commands.constants import (
    AURAUS,
    INFRAROAD,
    KUNTEC,
    LIUKKAUDENTORJUNTA,
)
from street_maintenance.models import DEFAULT_SRID, GeometryHistory

UTC_TIMEZONE = pytz.timezone("UTC")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def geometry_historys():
    geometry_historys = []
    now = datetime.now(UTC_TIMEZONE)
    geometry = LineString((0, 0), (0, 50), (50, 50), (50, 0), (0, 0), sird=DEFAULT_SRID)
    obj = GeometryHistory.objects.create(
        timestamp=now,
        geometry=geometry,
        coordinates=geometry.coords,
        provider=INFRAROAD,
        events=[AURAUS],
    )
    geometry_historys.append(obj)
    obj = GeometryHistory.objects.create(
        timestamp=now - timedelta(days=1),
        geometry=geometry,
        coordinates=geometry.coords,
        provider=INFRAROAD,
        events=[AURAUS],
    )
    geometry_historys.append(obj)

    obj = GeometryHistory.objects.create(
        timestamp=now - timedelta(days=2),
        geometry=geometry,
        coordinates=geometry.coords,
        provider=INFRAROAD,
        events=[LIUKKAUDENTORJUNTA],
    )
    geometry_historys.append(obj)

    obj = GeometryHistory.objects.create(
        timestamp=now - timedelta(days=1),
        geometry=geometry,
        coordinates=geometry.coords,
        provider=KUNTEC,
        events=[AURAUS],
    )

    geometry_historys.append(obj)
    obj = GeometryHistory.objects.create(
        timestamp=now - timedelta(days=2),
        geometry=geometry,
        coordinates=geometry.coords,
        provider=KUNTEC,
        events=[AURAUS, LIUKKAUDENTORJUNTA],
    )
    geometry_historys.append(obj)
    return geometry_historys
