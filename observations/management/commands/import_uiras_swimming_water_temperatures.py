"""
Management command: import_uiras_swimming_water_temperatures

Fetches current water temperatures from the UiRas API and stores them as
MeasuredObservation records linked to the uiras_swimming_water_temperature
ObservableProperty. Only units configured in settings.UIRAS_OBSERVABLE_UNITS
(Unit ID -> UiRas feature id) are imported.

Usage:
    python manage.py import_uiras_swimming_water_temperatures
    python manage.py import_uiras_swimming_water_temperatures --dry-run
"""

import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from observations.models import ObservableProperty
from observations.swimming_temperatures import parse_measurement, store_observation
from services.models import Unit

logger = logging.getLogger(__name__)

PROPERTY_ID = "uiras_swimming_water_temperature"


class Command(BaseCommand):
    help = (
        "Fetch swimming place water temperatures from the UiRas API and store "
        "them as measured observations."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch data but do not write anything to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        url = settings.UIRAS_BASE_URL
        unit_feature_map = settings.UIRAS_OBSERVABLE_UNITS or {}

        if not unit_feature_map:
            raise CommandError(
                "settings.UIRAS_OBSERVABLE_UNITS is empty; nothing to import."
            )

        observable_property = self._get_property()
        known_unit_ids = self._known_unit_ids(unit_feature_map)

        self.stdout.write(
            self.style.NOTICE(
                f"Starting UiRas import for {len(known_unit_ids)} unit(s)"
                + (" [DRY RUN]" if dry_run else "")
            )
        )

        features_by_id = self._fetch_features(url)
        created, units_updated, errors = self._import_units(
            known_unit_ids,
            unit_feature_map,
            features_by_id,
            observable_property,
            dry_run,
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

    def _known_unit_ids(self, unit_feature_map):
        configured_ids = list(unit_feature_map.keys())
        known_unit_ids = set(
            Unit.objects.filter(id__in=configured_ids).values_list("id", flat=True)
        )
        missing = set(configured_ids) - known_unit_ids
        if missing:
            logger.warning(
                "Skipping %d configured unit(s) not present in the database: %s",
                len(missing),
                ", ".join(str(m) for m in sorted(missing)),
            )
        return known_unit_ids

    def _fetch_features(self, url):
        self.stdout.write(f"Fetching UiRas data from {url} …")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CommandError(f"Failed to fetch UiRas data: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise CommandError(f"Failed to parse UiRas JSON from {url}: {exc}") from exc

        features = data.get("features") if isinstance(data, dict) else None
        if not isinstance(features, list):
            raise CommandError(
                f"Unexpected UiRas format from {url}: expected a 'features' list. "
                f"Got: {type(data).__name__}."
            )

        features_by_id = {}
        for feature in features:
            if not isinstance(feature, dict):
                continue
            feature_id = feature.get("id") or (feature.get("properties") or {}).get(
                "id"
            )
            if feature_id is not None:
                features_by_id[str(feature_id)] = feature
        self.stdout.write(f"  Found {len(features_by_id)} feature(s) in UiRas data.")
        return features_by_id

    def _import_units(
        self,
        known_unit_ids,
        unit_feature_map,
        features_by_id,
        observable_property,
        dry_run,
    ):
        created = 0
        units_updated = 0
        errors = []
        for unit_id in sorted(known_unit_ids):
            feature = features_by_id.get(str(unit_feature_map[unit_id]))
            was_created = self._process_unit(
                unit_id, feature, observable_property, dry_run, errors
            )
            if was_created is None:
                continue
            if was_created:
                created += 1
            units_updated += 1
        return created, units_updated, errors

    def _process_unit(self, unit_id, feature, observable_property, dry_run, errors):
        result = self._resolve_measurement(unit_id, feature)
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

    def _resolve_measurement(self, unit_id, feature):
        if not isinstance(feature, dict):
            logger.warning("No UiRas feature configured/found for unit %s", unit_id)
            return None
        properties = feature.get("properties") or {}
        measurement = properties.get("measurement")
        return parse_measurement(measurement, unit_id)

    def _store_safe(
        self, unit_id, observable_property, temperature, measured_at, errors
    ):
        try:
            return store_observation(
                unit_id, observable_property, temperature, measured_at
            )
        except Exception as exc:  # noqa: BLE001
            msg = f"Failed to store observation for unit {unit_id}: {exc}"
            logger.error(msg)
            errors.append(msg)
            return None

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
