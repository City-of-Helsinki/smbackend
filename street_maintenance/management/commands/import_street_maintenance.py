import logging
import re
import zoneinfo
from datetime import datetime

import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

UNITS_URL = (
    "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/query?since=72hours"
)
DEFAULT_HISTORY_SIZE = 10000
WORKS_URL = "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/{id}?history={history_size}"

logger = logging.getLogger("street_maintenance")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--history_size",
            type=int,
            nargs="+",
            default=False,
            help=f"Max number of location history items to fetch per unit. Default {DEFAULT_HISTORY_SIZE}.",
        )

    def get_and_create_maintenance_units(self):
        response = requests.get(UNITS_URL)
        assert (
            response.status_code == 200
        ), "Fetching Maintenance Unit {} status code: {}".format(
            UNITS_URL, response.status_code
        )
        for unit in response.json():
            # TODO Check if geometry in Turku region
            MaintenanceUnit.objects.create(unit_id=unit["id"])
        logger.info(
            f"Imported {MaintenanceUnit.objects.all().count()} Mainetance Units."
        )

    def get_and_create_maintenance_works(self, history_size):
        works = []
        for unit in MaintenanceUnit.objects.all():
            response = requests.get(
                WORKS_URL.format(id=unit.unit_id, history_size=history_size)
            )
            if "location_history" in response.json():
                json_data = response.json()["location_history"]
            else:
                logger.warning(f"Location history not found for: {unit.unit_id}")
                continue
            for work in json_data:
                timestamp = datetime.strptime(
                    work["timestamp"], "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki"))
                coords = work["coords"]
                coords = [float(c) for c in re.sub(r"[()]", "", coords).split(" ")]
                point = Point(coords[0], coords[1], srid=DEFAULT_SRID)
                events = []
                for event in work["events"]:
                    events.append(event)
                works.append(
                    MaintenanceWork(
                        maintenance_unit=unit,
                        timestamp=timestamp,
                        point=point,
                        events=events,
                    )
                )
        MaintenanceWork.objects.bulk_create(works)
        logger.info(f"Imported {len(works)} Mainetance Works.")

    def handle(self, *args, **options):
        start_time = datetime.now()
        MaintenanceUnit.objects.all().delete()
        self.get_and_create_maintenance_units()
        if options["history_size"]:
            history_size = options["history_size"][0]
        else:
            history_size = DEFAULT_HISTORY_SIZE
        self.get_and_create_maintenance_works(history_size)
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Imported maintenance history in: {duration}")
