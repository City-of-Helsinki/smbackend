import logging
from datetime import datetime

from django.contrib.gis.geos import LineString
from django.core.management.base import BaseCommand

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

from .constants import (
    AUTORI_DEFAULT_WORKS_HISTORY_SIZE,
    AUTORI_MAX_WORKS_HISTORY_SIZE,
    EVENT_MAPPINGS,
)
from .utils import (
    create_autori_maintenance_units,
    create_dict_from_autori_events,
    get_autori_access_token,
    get_autori_contract,
    get_autori_event_types,
    get_autori_routes,
    get_turku_boundary,
)

TURKU_BOUNDARY = get_turku_boundary()
logger = logging.getLogger("street_maintenance")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--history-size",
            type=int,
            nargs="+",
            default=False,
            help="History size in days.",
        )

    def get_and_create_autori_maintenance_works(self, history_size=None):
        access_token = get_autori_access_token()
        create_autori_maintenance_units(access_token)
        contract = get_autori_contract(access_token)
        list_of_events = get_autori_event_types(access_token)
        event_name_mappings = create_dict_from_autori_events(list_of_events)
        routes = get_autori_routes(access_token, contract, history_size)
        works = []
        for route in routes:
            if len(route["geography"]["features"]) > 1:
                logger.warning(
                    f"Route contains multiple features. {route['geography']['features']}"
                )
            coordinates = route["geography"]["features"][0]["geometry"]["coordinates"]
            geometry = LineString(coordinates, srid=DEFAULT_SRID)
            if not TURKU_BOUNDARY.covers(geometry):
                continue

            events = []
            operations = route["operations"]
            for operation in operations:
                event_name = event_name_mappings[operation]
                events.append(EVENT_MAPPINGS[event_name])
            if len(route["geography"]["features"]) > 1:
                logger.warning(
                    f"Route contains multiple features. {route['geography']['features']}"
                )
            unit_id = route["vehicleType"]
            try:
                unit = MaintenanceUnit.objects.get(unit_id=unit_id)
            except MaintenanceUnit.DoesNotExist:
                logger.warning(f"Maintenance unit: {unit_id}, not found.")
                continue
            works.append(
                MaintenanceWork(
                    timestamp=route["startTime"],
                    maintenance_unit=unit,
                    events=events,
                    geometry=geometry,
                )
            )

        MaintenanceWork.objects.bulk_create(works)
        logger.info(f"Imported {len(works)} Autori(YIT) mainetance works.")

    def handle(self, *args, **options):
        importer_start_time = datetime.now()
        MaintenanceUnit.objects.filter(provider=MaintenanceUnit.AUTORI).delete()
        history_size = AUTORI_DEFAULT_WORKS_HISTORY_SIZE
        if options["history_size"]:
            history_size = int(options["history_size"][0])
            if history_size > AUTORI_MAX_WORKS_HISTORY_SIZE:
                error_msg = f"Max value for the history size is: {AUTORI_MAX_WORKS_HISTORY_SIZE}"
                raise ValueError(error_msg)

        self.get_and_create_autori_maintenance_works(history_size=history_size)
        importer_end_time = datetime.now()
        duration = importer_end_time - importer_start_time
        logger.info(f"Imported Autori(YIT) street maintenance history in: {duration}")
