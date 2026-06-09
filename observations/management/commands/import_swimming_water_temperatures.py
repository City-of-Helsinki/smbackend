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

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from observations.models import ObservableProperty
from observations.swimming_temperatures import parse_measurement, store_observation
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
            return store_observation(
                unit_id, observable_property, temperature, measured_at
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to store observation for unit {unit_id}: {exc}"
            logger.error(msg)
            errors.append(msg)
            return None

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
            properties = response.json().get("properties") or {}
            return parse_measurement(properties.get("measurement"), unit_id)
        except requests.RequestException as exc:
            logger.warning(
                "Could not fetch data for unit %s from %s: %s", unit_id, url, exc
            )
            return None
