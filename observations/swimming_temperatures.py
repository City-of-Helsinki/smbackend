"""Shared helpers for importing swimming water temperatures from the
sensoripaja.fi and UiRas import management commands.
"""

import logging
import math
from datetime import UTC

from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware

from observations.models import MeasuredObservation, UnitLatestObservation

logger = logging.getLogger(__name__)


def parse_measurement(measurement, unit_id):
    """Parse a measurement dict into (temperature, measured_at), or None."""
    if not measurement:
        logger.debug("No measurement block for unit %s", unit_id)
        return None

    raw_temp = measurement.get("temp_water")
    time_raw = measurement.get("time")
    measured_at = parse_datetime(str(time_raw)) if time_raw is not None else None
    try:
        temp_water = float(raw_temp) if raw_temp is not None else None
    except (ValueError, TypeError):
        temp_water = None

    if temp_water is not None and not math.isfinite(temp_water):
        temp_water = None

    if temp_water is None or measured_at is None:
        logger.warning(
            "Incomplete measurement for unit %s: temp_water=%r, time=%r",
            unit_id,
            raw_temp,
            time_raw,
        )
        return None

    if not is_aware(measured_at):
        measured_at = make_aware(measured_at, UTC)

    return temp_water, measured_at


@transaction.atomic
def store_observation(unit_id, observable_property, temperature, measured_at) -> bool:
    """Store a reading idempotently and update the unit's latest pointer.

    Returns True if a new observation row was created.
    """
    observation, created = MeasuredObservation.objects.get_or_create(
        unit_id=unit_id,
        property=observable_property,
        time=measured_at,
        defaults={"measured_value": temperature},
    )
    if not created and observation.measured_value != temperature:
        observation.measured_value = temperature
        observation.save(update_fields=["measured_value"])

    latest = (
        MeasuredObservation.objects.filter(
            unit_id=unit_id, property=observable_property
        )
        .order_by("-time")
        .first()
    )
    UnitLatestObservation.objects.update_or_create(
        unit_id=unit_id,
        property=observable_property,
        defaults={"observation_id": latest.pk},
    )
    return created
