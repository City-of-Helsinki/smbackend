from unittest import mock

import pytest
from django.core.management import call_command
from django.test import override_settings
from fixtures import *  # noqa: F401,F403

from observations.models import MeasuredObservation, UnitLatestObservation

COMMAND = "import_uiras_swimming_water_temperatures"
MODULE = "observations.management.commands.import_uiras_swimming_water_temperatures"

FEATURE_ID = "70B3D57050001ADA"


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def make_requests_get(payload):
    def _get(url, *args, **kwargs):
        return FakeResponse(payload)

    return _get


def feature(feature_id, temp, time):
    return {
        "id": feature_id,
        "type": "Feature",
        "properties": {"measurement": {"temp_water": temp, "time": time}},
    }


def feature_collection(features):
    return {"type": "FeatureCollection", "features": features}


@pytest.mark.django_db
@override_settings(UIRAS_OBSERVABLE_UNITS={1: FEATURE_ID})
def test__command_imports_measured_observation(unit, uiras_property):
    payload = feature_collection(
        [feature(FEATURE_ID, 13.25, "2026-06-05T12:08:34+03:00")]
    )

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(payload)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 1
    obs = MeasuredObservation.objects.get(unit=unit)
    assert obs.measured_value == pytest.approx(13.25)
    latest = UnitLatestObservation.objects.get(unit=unit, property=uiras_property)
    assert latest.observation_id == obs.pk


@pytest.mark.django_db
@override_settings(UIRAS_OBSERVABLE_UNITS={1: FEATURE_ID})
def test__command_is_idempotent_and_tracks_latest(unit, uiras_property):
    first = feature_collection(
        [feature(FEATURE_ID, 13.25, "2026-06-05T12:08:34+03:00")]
    )
    with mock.patch(f"{MODULE}.requests.get", make_requests_get(first)):
        call_command(COMMAND)
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 1

    second = feature_collection(
        [feature(FEATURE_ID, 14.10, "2026-06-05T12:28:34+03:00")]
    )
    with mock.patch(f"{MODULE}.requests.get", make_requests_get(second)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 2
    latest = UnitLatestObservation.objects.get(unit=unit, property=uiras_property)
    latest_obs = MeasuredObservation.objects.get(pk=latest.observation_id)
    assert latest_obs.measured_value == pytest.approx(14.10)


@pytest.mark.django_db
@override_settings(UIRAS_OBSERVABLE_UNITS={1: FEATURE_ID})
def test__command_dry_run_writes_nothing(unit, uiras_property):
    payload = feature_collection(
        [feature(FEATURE_ID, 13.25, "2026-06-05T12:08:34+03:00")]
    )

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(payload)):
        call_command(COMMAND, "--dry-run")

    assert MeasuredObservation.objects.count() == 0
    assert UnitLatestObservation.objects.count() == 0


@pytest.mark.django_db
@override_settings(UIRAS_OBSERVABLE_UNITS={1: FEATURE_ID, 99999999: "DEADBEEF"})
def test__command_skips_units_not_in_db(unit, uiras_property):
    payload = feature_collection(
        [
            feature(FEATURE_ID, 13.25, "2026-06-05T12:08:34+03:00"),
            feature("DEADBEEF", 9.9, "2026-06-05T12:08:34+03:00"),
        ]
    )

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(payload)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.filter(unit=unit).count() == 1
    assert MeasuredObservation.objects.count() == 1


@pytest.mark.django_db
@override_settings(UIRAS_OBSERVABLE_UNITS={1: FEATURE_ID})
def test__command_handles_missing_feature(unit, uiras_property):
    payload = feature_collection(
        [feature("SOMETHING_ELSE", 13.25, "2026-06-05T12:08:34+03:00")]
    )

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(payload)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.count() == 0


@pytest.mark.django_db
@override_settings(UIRAS_OBSERVABLE_UNITS={1: FEATURE_ID})
def test__command_handles_null_properties(unit, uiras_property):
    payload = feature_collection([{"id": FEATURE_ID, "properties": None}])

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(payload)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.count() == 0


@pytest.mark.django_db
@override_settings(UIRAS_OBSERVABLE_UNITS={1: FEATURE_ID})
def test__command_handles_missing_temp_water(unit, uiras_property):
    payload = feature_collection(
        [
            {
                "id": FEATURE_ID,
                "properties": {"measurement": {"time": "2026-06-05T12:08:34+03:00"}},
            }
        ]
    )

    with mock.patch(f"{MODULE}.requests.get", make_requests_get(payload)):
        call_command(COMMAND)

    assert MeasuredObservation.objects.count() == 0
