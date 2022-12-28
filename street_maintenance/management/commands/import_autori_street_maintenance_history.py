import logging

from django.contrib.gis.geos import LineString

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

from .base_import_command import BaseImportCommand
from .constants import (
    AUTORI,
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
    is_nested_coordinates,
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

    def create_autori_maintenance_works(self, history_size=None):
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
            if is_nested_coordinates(coordinates) and len(coordinates) > 1:
                geometry = LineString(coordinates, srid=DEFAULT_SRID)
            else:
                # Remove other data, contains faulty linestrings.
                continue

            if not TURKU_BOUNDARY.covers(geometry):
                continue

            events = []
            operations = route["operations"]
            for operation in operations:
                event_name = event_name_mappings[operation].lower()
                if event_name in EVENT_MAPPINGS:
                    for e in EVENT_MAPPINGS[event_name]:
                        # If mapping value is None, the event is not used.
                        if e:
                            events.append(e)
                else:
                    logger.warning(
                        f"Found unmapped event: {event_name_mappings[operation]}"
                    )

            # If no events found discard the work
            if len(events) == 0:
                continue
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
        return len(works)

    def handle(self, *args, **options):
        super().__init__()
        MaintenanceUnit.objects.filter(provider=AUTORI).delete()
        history_size = AUTORI_DEFAULT_WORKS_HISTORY_SIZE
        if options["history_size"]:
            history_size = int(options["history_size"][0])
            if history_size > AUTORI_MAX_WORKS_HISTORY_SIZE:
                error_msg = f"Max value for the history size is: {AUTORI_MAX_WORKS_HISTORY_SIZE}"
                raise ValueError(error_msg)

        works_created = self.create_autori_maintenance_works(history_size=history_size)
        # In some unknown(erroneous server?) cases no data for works is availale. In that case we want to store
        # the previeus state of the precalculated geometry history data.
        if works_created > 0:
            precalculate_geometry_history(AUTORI)
        else:
            logger.warning(
                f"No works created for {AUTORI}(YIT), skipping geometry history population."
            )
        super().display_duration(AUTORI)
