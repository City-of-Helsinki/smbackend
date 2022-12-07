import logging
import re
import zoneinfo
from datetime import datetime

import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

from .constants import (
    EVENT_MAPPINGS,
    INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE,
    INFRAROAD_WORKS_URL,
)
from .utils import create_infraroad_maintenance_units, get_turku_boundary

logger = logging.getLogger("street_maintenance")
TURKU_BOUNDARY = get_turku_boundary()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--history-size",
            type=int,
            nargs="+",
            default=False,
            help=(
                "Max number of location history items to fetch per unit."
                + "Default {INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE}."
            ),
        )

    def create_infraroad_maintenance_works(self, history_size):
        create_infraroad_maintenance_units()
        works = []
        for unit in MaintenanceUnit.objects.filter(provider=MaintenanceUnit.INFRAROAD):
            response = requests.get(
                INFRAROAD_WORKS_URL.format(id=unit.unit_id, history_size=history_size)
            )
            if "location_history" in response.json():
                json_data = response.json()["location_history"]
            else:
                logger.warning(f"Location history not found for unit: {unit.unit_id}")
                continue
            for work in json_data:
                coords = work["coords"]
                coords = [float(c) for c in re.sub(r"[()]", "", coords).split(" ")]
                point = Point(coords[0], coords[1], srid=DEFAULT_SRID)
                # discard events outside Turku.
                if not TURKU_BOUNDARY.covers(point):
                    continue

                timestamp = datetime.strptime(
                    work["timestamp"], "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki"))

                events = []
                for event in work["events"]:
                    event_name = event.lower()
                    if event_name in EVENT_MAPPINGS:
                        for e in EVENT_MAPPINGS[event_name]:
                            # If mapping value is None, the event is not used.
                            if e:
                                events.append(e)
                    else:
                        logger.warning(f"Found unmapped event: {event}")
                # If no events found discard the work
                if len(events) == 0:
                    continue
                works.append(
                    MaintenanceWork(
                        timestamp=timestamp,
                        maintenance_unit=unit,
                        geometry=point,
                        events=events,
                    )
                )
        MaintenanceWork.objects.bulk_create(works)
        logger.info(f"Imported {len(works)} Infraroad mainetance works.")

    def handle(self, *args, **options):
        importer_start_time = datetime.now()
        MaintenanceUnit.objects.filter(provider=MaintenanceUnit.INFRAROAD).delete()
        if options["history_size"]:
            history_size = options["history_size"][0]
        else:
            history_size = INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE
        self.create_infraroad_maintenance_works(history_size)
        importer_end_time = datetime.now()
        duration = importer_end_time - importer_start_time
        logger.info(f"Imported Infraroad street maintenance history in: {duration}")
