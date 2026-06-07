from unittest import mock

import pytest
from django.core.management import call_command
from fixtures import *  # noqa: F401,F403

from observations.models import MeasuredObservation, UnitLatestObservation

COMMAND = "import_swimming_water_temperatures"
MODULE = "observations.management.commands.import_swimming_water_temperatures"


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def make_requests_get(index_payload, geojson_by_unit):
    def _get(url, *args, **kwargs):
        if url.endswith("tprId-index.json"):
            return FakeResponse(index_payload)
        for unit_id, payload in geojson_by_unit.items():
            if url.endswith(f"/{unit_id}.geojson"):
                return FakeResponse(payload)
        raise AssertionError(f"Unexpected URL requested: {url}")

    return _get


def geojson(temp, time):
    return {"properties": {"measurement": {"temp_water": temp, "time": time}}}


@pytest.mark.django_db
def test__command_imports_measured_observation(unit, measured_property):
    index = {"type": "index", "key": "tprId", "items": {str(unit.pk): "Test Beach"}}
    payloads = {unit.pk: geojson(13.25, "2026-06-05T12:08:34+03:00")}

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(index, payloads)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 1
    obs = MeasuredObservation.objects.get(unit=unit)
    assert obs.measured_value == pytest.approx(13.25)
    latest = UnitLatestObservation.objects.get(unit=unit, property=measured_property)
    assert latest.observation_id == obs.pk


@pytest.mark.django_db
def test__command_is_idempotent_and_tracks_latest(unit, measured_property):
    index = {"items": {str(unit.pk): "Test Beach"}}

    first = {unit.pk: geojson(13.25, "2026-06-05T12:08:34+03:00")}
    with mock.patch(f"{MODULE}.requests.get", make_requests_get(index, first)):
        call_command(COMMAND)
        # Re-running with the same reading creates no duplicate.
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 1

    # A newer reading is appended and becomes the latest.
    second = {unit.pk: geojson(14.10, "2026-06-05T12:28:34+03:00")}
    with mock.patch(f"{MODULE}.requests.get", make_requests_get(index, second)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 2
    latest = UnitLatestObservation.objects.get(unit=unit, property=measured_property)
    latest_obs = MeasuredObservation.objects.get(pk=latest.observation_id)
    assert latest_obs.measured_value == pytest.approx(14.10)


@pytest.mark.django_db
def test__command_dry_run_writes_nothing(unit, measured_property):
    index = {"items": {str(unit.pk): "Test Beach"}}
    payloads = {unit.pk: geojson(13.25, "2026-06-05T12:08:34+03:00")}

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(index, payloads)):
        call_command(COMMAND, "--dry-run")

    assert MeasuredObservation.objects.count() == 0
    assert UnitLatestObservation.objects.count() == 0


@pytest.mark.django_db
def test__command_skips_units_not_in_db(unit, measured_property):
    index = {"items": {"99999999": "Unknown", str(unit.pk): "Test Beach"}}
    payloads = {unit.pk: geojson(13.25, "2026-06-05T12:08:34+03:00")}

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(index, payloads)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 1
    assert MeasuredObservation.objects.count() == 1


@pytest.mark.django_db
def test__command_handles_missing_measurement(unit, measured_property):
    index = {"items": {str(unit.pk): "Test Beach"}}
    payloads = {unit.pk: {"properties": {}}}  # no measurement block

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(index, payloads)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.count() == 0


@pytest.mark.django_db
def test__command_handles_missing_temp_water(unit, measured_property):
    index = {"items": {str(unit.pk): "Test Beach"}}
    payloads = {
        unit.pk: {"properties": {"measurement": {"time": "2026-06-05T12:08:34+03:00"}}}
    }

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(index, payloads)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.count() == 0
