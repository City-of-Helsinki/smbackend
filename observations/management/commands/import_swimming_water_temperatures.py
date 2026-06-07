"""
Management command: import_swimming_water_temperatures

Fetches current water temperatures from the sensoripaja.fi API and stores them
as MeasuredObservation records linked to the measured_swimming_water_temperature
ObservableProperty. The latest reading per unit is recorded in
UnitLatestObservation and exposed through the /v2/observation endpoint.

Usage:
    python manage.py import_swimming_water_temperatures
    python manage.py import_swimming_water_temperatures --unit-ids 40258,40157
    python manage.py import_swimming_water_temperatures --dry-run
"""

import logging
from datetime import UTC

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware

from observations.models import (
    MeasuredObservation,
    ObservableProperty,
    UnitLatestObservation,
)
from services.models import Unit

logger = logging.getLogger(__name__)

PROPERTY_ID = "measured_swimming_water_temperature"


class Command(BaseCommand):
    help = (
        "Fetch swimming place water temperatures from sensoripaja.fi and store "
        "them as measured observations."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--unit-ids",
            type=str,
            default="",
            metavar="ID1,ID2,...",
            help=(
                "Comma-separated list of Unit IDs (tprIds) to import.  "
                "Defaults to all IDs returned by the tprId-index.json endpoint."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch data but do not write anything to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        base_url = settings.SWIMMING_TEMPERATURES_BASE_URL.rstrip("/")

        observable_property = self._get_property()
        known_unit_ids = self._resolve_known_unit_ids(options["unit_ids"], base_url)

        self.stdout.write(
            self.style.NOTICE(
                f"Starting import for {len(known_unit_ids)} unit(s)"
                + (" [DRY RUN]" if dry_run else "")
            )
        )

        created, units_updated, errors = self._import_units(
            sorted(known_unit_ids), base_url, observable_property, dry_run
        )
        self._report(created, units_updated, errors)

    def _get_property(self):
        try:
            return ObservableProperty.objects.get(pk=PROPERTY_ID)
        except ObservableProperty.DoesNotExist as exc:
            raise CommandError(
                f"ObservableProperty '{PROPERTY_ID}' does not exist. "
                "Run migrations or load the observation fixtures first."
            ) from exc

    def _resolve_known_unit_ids(self, unit_ids_arg, base_url):
        unit_ids = self._resolve_unit_ids(unit_ids_arg, base_url)
        if not unit_ids:
            raise CommandError(
                "No unit IDs found.  The index endpoint returned an empty list "
                "and no --unit-ids override was provided."
            )

        known_unit_ids = set(
            Unit.objects.filter(id__in=unit_ids).values_list("id", flat=True)
        )
        missing = set(unit_ids) - known_unit_ids
        if missing:
            logger.warning(
                "Skipping %d unit(s) not present in the database: %s",
                len(missing),
                ", ".join(str(m) for m in sorted(missing)),
            )
        return known_unit_ids

    def _import_units(self, unit_ids, base_url, observable_property, dry_run):
        created = 0
        units_updated = 0
        errors = []
        for unit_id in unit_ids:
            was_created = self._process_unit(
                unit_id, base_url, observable_property, dry_run, errors
            )
            if was_created is None:
                continue
            if was_created:
                created += 1
            units_updated += 1
        return created, units_updated, errors

    def _report(self, created, units_updated, errors):
        if errors:
            self.stderr.write(
                self.style.ERROR(f"Completed with {len(errors)} error(s):")
            )
            for err in errors:
                self.stderr.write(f"  {err}")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. {created} new reading(s) stored, "
                    f"{units_updated} unit(s) updated."
                )
            )

    def _process_unit(self, unit_id, base_url, observable_property, dry_run, errors):
        """Fetch and store one unit's reading.

        Returns True/False for created/updated, or None if skipped or failed.
        """
        result = self._fetch_safe(unit_id, base_url, errors)
        if result is None:
            return None
        temperature, measured_at = result
        if dry_run:
            self.stdout.write(
                f"  [dry-run] unit={unit_id} temp={temperature}°C at {measured_at}"
            )
            return None
        return self._store_safe(
            unit_id, observable_property, temperature, measured_at, errors
        )

    def _fetch_safe(self, unit_id, base_url, errors):
        """Fetch temperature for a unit.

        Network errors are warned and skipped (returns None).
        Unexpected exceptions are logged as errors and appended to errors.
        """
        try:
            return self._fetch_unit_temperature(unit_id, base_url)
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to fetch unit {unit_id}: {exc}"
            logger.error(msg)
            errors.append(msg)
            return None

    def _store_safe(
        self, unit_id, observable_property, temperature, measured_at, errors
    ):
        """Store an observation, appending to errors on failure."""
        try:
            return self._store_observation(
                unit_id, observable_property, temperature, measured_at
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to store observation for unit {unit_id}: {exc}"
            logger.error(msg)
            errors.append(msg)
            return None

    @transaction.atomic
    def _store_observation(
        self, unit_id, observable_property, temperature, measured_at
    ) -> bool:
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

    def _resolve_unit_ids(self, unit_ids_arg: str, base_url: str) -> list[int]:
        """Return unit IDs from --unit-ids, or the live tprId index."""
        if unit_ids_arg:
            ids, invalid = [], []
            for token in unit_ids_arg.split(","):
                token = token.strip()
                try:
                    ids.append(int(token))
                except ValueError:
                    invalid.append(token)
            if invalid:
                raise CommandError(
                    f"Invalid unit ID(s) in --unit-ids: "
                    f"{', '.join(repr(t) for t in invalid)}"
                )
            return ids

        index_url = f"{base_url}/tprId-index.json"
        self.stdout.write(f"Fetching unit index from {index_url} …")
        try:
            response = requests.get(index_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CommandError(f"Failed to fetch unit index: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise CommandError(
                f"Failed to parse index JSON from {index_url}: {exc}"
            ) from exc
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, dict):
            raise CommandError(
                f"Unexpected index format from {index_url}: expected an 'items' "
                f"object. Got: {type(data).__name__}."
            )

        ids = []
        for tpr_id in items.keys():
            try:
                ids.append(int(tpr_id))
            except (ValueError, TypeError):
                logger.warning("Non-integer tprId in index: %s", tpr_id)
        self.stdout.write(f"  Found {len(ids)} unit(s) in index.")
        return ids

    def _fetch_unit_temperature(self, unit_id: int, base_url: str):
        """Return (temperature, measured_at) for a unit, or None if unavailable."""
        url = f"{base_url}/{unit_id}.geojson"
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            properties = response.json().get("properties", {})
            return self._parse_measurement(properties.get("measurement"), unit_id)
        except requests.RequestException as exc:
            logger.warning(
                "Could not fetch data for unit %s from %s: %s", unit_id, url, exc
            )
            return None

    def _parse_measurement(self, measurement, unit_id):
        """Parse a measurement dict into (temperature, measured_at), or None."""
        if not measurement:
            logger.debug("No measurement block for unit %s", unit_id)
            return None

        time_raw = measurement.get("time")
        measured_at = parse_datetime(str(time_raw)) if time_raw is not None else None
        try:
            temp_water = float(measurement.get("temp_water"))
        except (ValueError, TypeError):
            temp_water = None

        if temp_water is None or measured_at is None:
            logger.warning(
                "Incomplete or invalid measurement for unit %s: temp_water=%r, time=%r",
                unit_id,
                measurement.get("temp_water"),
                time_raw,
            )
            return None

        if not is_aware(measured_at):
            measured_at = make_aware(measured_at, UTC)

        return temp_water, measured_at
