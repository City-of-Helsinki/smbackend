import logging
import re
import zoneinfo
from datetime import datetime

import requests
from django.contrib.gis.geos import LineString, Point
from django.core.management.base import BaseCommand

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

from .constants import EVENT_MAPPINGS, INFRAROAD_WORKS_URL
from .utils import (
    create_dict_from_autori_events,
    create_infraroad_maintenance_units,
    get_autori_access_token,
    get_autori_contract,
    get_autori_event_types,
    get_autori_routes,
    get_turku_boundary,
)

INFRAROAD_DEFAULT_HISTORY_SIZE = 10000

logger = logging.getLogger("street_maintenance")

TURKU_BOUNDARY = get_turku_boundary()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--infraroad-history-size",
            type=int,
            nargs="+",
            default=False,
            help=f"Max number of location history items to fetch per unit. Default {INFRAROAD_DEFAULT_HISTORY_SIZE}.",
        )

    def get_and_create_infraroad_maintenance_works(self, history_size):
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
                    if event in EVENT_MAPPINGS:
                        events.append(EVENT_MAPPINGS[event])
                    else:
                        logger.warning(f"Found unmapped event: {event}")
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

    def get_and_create_autori_maintenance_works(self):
        # Yit
        access_token = get_autori_access_token()
        contract = get_autori_contract(access_token)
        list_of_events = get_autori_event_types(access_token)
        event_name_mappings = create_dict_from_autori_events(list_of_events)
        routes = get_autori_routes(access_token, contract)
        works = []
        for route in routes:
            if len(route["geography"]["features"]) > 1:
                logger.warning(
                    f"Route contains multiple features. {route['geography']['features']}"
                )
            coordinates = route["geography"]["features"][0]["geometry"]["coordinates"]
            geometry = LineString(coordinates, srid=DEFAULT_SRID)

            # TODO fix this
            # if not TURKU_BOUNDARY.covers(geometry):
            #     print("YIT not in turku")
            #     continue

            events = []
            operations = route["operations"]
            for operation in operations:
                event_name = event_name_mappings[operation]
                events.append(EVENT_MAPPINGS[event_name])
            if len(route["geography"]["features"]) > 1:
                logger.warning(
                    f"Route contains multiple features. {route['geography']['features']}"
                )
            works.append(
                MaintenanceWork(
                    timestamp=route["startTime"],
                    events=events,
                    geometry=geometry,
                )
            )

        MaintenanceWork.objects.bulk_create(works)
        logger.info(f"Imported {len(works)} Autori(YIT) mainetance works.")

    def handle(self, *args, **options):
        start_time = datetime.now()
        MaintenanceUnit.objects.all().delete()
        # Delete also all works as, there might be works that do not have a relation to a Unit.
        MaintenanceWork.objects.all().delete()

        # Infraroad
        if options["infraroad_history_size"]:
            history_size = options["infraroad_history_size"][0]
        else:
            history_size = INFRAROAD_DEFAULT_HISTORY_SIZE
        self.get_and_create_infraroad_maintenance_works(history_size)
        # Autori(YIT)
        self.get_and_create_autori_maintenance_works()

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Imported street maintenance history in: {duration}")
