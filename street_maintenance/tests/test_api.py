from datetime import datetime, timedelta

import pytest
import pytz
from rest_framework.reverse import reverse

from street_maintenance.management.commands.constants import (
    AURAUS,
    INFRAROAD,
    KUNTEC,
    LIUKKAUDENTORJUNTA,
    START_DATE_TIME_FORMAT,
)

UTC_TIMEZONE = pytz.timezone("UTC")


@pytest.mark.django_db
def test_geometry_history(api_client, geometry_historys):
    url = reverse("street_maintenance:geometry_history-list")
    response = api_client.get(url)
    assert response.json()["count"] == 5
    # Test provider parameter
    url = reverse("street_maintenance:geometry_history-list") + f"?provider={KUNTEC}"
    response = api_client.get(url)
    # Fixture data contains 2 KUNTEC GeometryHistroy rows
    assert response.json()["count"] == 2
    # Test event parameter
    url = reverse("street_maintenance:geometry_history-list") + f"?event={AURAUS}"
    response = api_client.get(url)
    # 3 INFRAROAD AURAUS events and 1 KUNTEC
    assert response.json()["count"] == 4
    # Test event and provider parameter
    url = (
        reverse("street_maintenance:geometry_history-list")
        + f"?provider={KUNTEC}&event={LIUKKAUDENTORJUNTA}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 1
    # test start_date_time parameter
    start_date_time = datetime.now(UTC_TIMEZONE) - timedelta(hours=1)
    url = (
        reverse("street_maintenance:geometry_history-list")
        + f"?start_date_time={start_date_time.strftime(START_DATE_TIME_FORMAT)}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 1
    geometry_history = response.json()["results"][0]
    assert geometry_history["geometry_type"] == "LineString"
    assert geometry_history["provider"] == INFRAROAD
    start_date_time = datetime.now(UTC_TIMEZONE) - timedelta(days=1)
    url = (
        reverse("street_maintenance:geometry_history-list")
        + f"?start_date_time={start_date_time.strftime(START_DATE_TIME_FORMAT)}"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 3
