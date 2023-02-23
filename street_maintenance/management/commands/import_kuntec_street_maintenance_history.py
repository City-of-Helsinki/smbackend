import logging
from datetime import datetime, timedelta

import polyline
import requests
from django.conf import settings
from django.contrib.gis.geos import LineString

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

# from django.core.management.base import BaseCommand
from .base_import_command import BaseImportCommand
from .constants import (
    EVENT_MAPPINGS,
    KUNTEC,
    KUNTEC_DEFAULT_WORKS_HISTORY_SIZE,
    KUNTEC_KEY,
    KUNTEC_MAX_WORKS_HISTORY_SIZE,
    TIMESTAMP_FORMATS,
    URLS,
    WORKS,
)
from .utils import (
    create_kuntec_maintenance_units,
    get_linestring_in_boundary,
    get_turku_boundary,
    precalculate_geometry_history,
)

TURKU_BOUNDARY = get_turku_boundary()
logger = logging.getLogger("street_maintenance")


class Command(BaseImportCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--history-size",
            type=int,
            nargs="+",
            default=False,
            help="History size in days.",
        )

    def create_kuntec_maintenance_works(self, history_size=None):
        num_created = 0
        now = datetime.now()
        start = (now - timedelta(days=history_size)).strftime(TIMESTAMP_FORMATS[KUNTEC])
        end = now.strftime(TIMESTAMP_FORMATS[KUNTEC])
        ids_to_delete = list(
            MaintenanceUnit.objects.filter(provider=KUNTEC).values_list("id", flat=True)
        )
        for unit in MaintenanceUnit.objects.filter(provider=KUNTEC):
            url = URLS[KUNTEC][WORKS].format(
                key=KUNTEC_KEY, start=start, end=end, unit_id=unit.unit_id
            )
            response = requests.get(url)
            if response.status_code != 200:
                continue
            if "data" in response.json():
                for units in response.json()["data"]["units"]:
                    for route in units["routes"]:
                        events = []
                        original_event_names = []
                        # Routes of type 'stop' are discarded.
                        if route["type"] == "route":
                            # Check for mapped events to include as works.
                            for name in unit.names:
                                event_name = name.lower()
                                if event_name in EVENT_MAPPINGS:
                                    for e in EVENT_MAPPINGS[event_name]:
                                        # If mapping value is None, the event is not used.
                                        if e:
                                            events.append(e)
                                            original_event_names.append(name)
                                else:
                                    logger.warning(
                                        f"Found unmapped event: {event_name}"
                                    )
                        # If route has mapped event(s) and contains a polyline add work.
                        if len(events) > 0 and "polyline" in route:
                            coords = polyline.decode(route["polyline"], geojson=True)
                            if len(coords) > 1:
                                geometry = LineString(coords, srid=DEFAULT_SRID)
                            else:
                                continue
                            # Create linestring that is inside the boundary of Turku
                            # and discard parts of the geometry if they are outside the boundary.
                            geometry = get_linestring_in_boundary(
                                geometry, TURKU_BOUNDARY
                            )
                            if not geometry:
                                continue
                            timestamp = route["start"]["time"]

                            obj, created = MaintenanceWork.objects.get_or_create(
                                timestamp=timestamp,
                                maintenance_unit=unit,
                                events=events,
                                original_event_names=original_event_names,
                                geometry=geometry,
                            )
                            if obj.id in ids_to_delete:
                                ids_to_delete.remove(obj.id)
                            if created:
                                num_created += 1

        MaintenanceWork.objects.filter(id__in=ids_to_delete).delete()
        num_works = MaintenanceWork.objects.filter(
            maintenance_unit__provider=KUNTEC
        ).count()
        logger.info(
            f"Deleted {len(ids_to_delete)} obsolete Works for provider {KUNTEC}"
        )
        logger.info(
            f"Created {num_created} Works of total {num_works} Works for provider {KUNTEC}."
        )
        return num_created

    def handle(self, *args, **options):
        super().__init__()
        assert settings.KUNTEC_KEY, "KUNTEC_KEY not found in environment."
        MaintenanceWork.objects.filter(maintenance_unit__provider=KUNTEC).delete()
        history_size = KUNTEC_DEFAULT_WORKS_HISTORY_SIZE
        if options["history_size"]:
            history_size = int(options["history_size"][0])
            if history_size > KUNTEC_MAX_WORKS_HISTORY_SIZE:
                error_msg = f"Max value for the history size is: {KUNTEC_MAX_WORKS_HISTORY_SIZE}"
                raise ValueError(error_msg)
        create_kuntec_maintenance_units()
        works_created = self.create_kuntec_maintenance_works(history_size=history_size)

        # In some unknown(erroneous mapon server?) cases, there are no works with route and/or Unit with io_din
        # Status 'On'(1) even if in reality there are. In that case we want to store the previeus state of the
        # precalculated geometry history for Kuntec data.
        if works_created > 0:
            precalculate_geometry_history(KUNTEC)
        else:
            logger.warning(
                f"No works created for {KUNTEC}, skipping geometry history population."
            )
        super().display_duration(KUNTEC)
