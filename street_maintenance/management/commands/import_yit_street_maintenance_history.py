import logging

from django.contrib.gis.geos import LineString

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

from .base_import_command import BaseImportCommand
from .constants import (
    EVENT_MAPPINGS,
    YIT,
    YIT_DEFAULT_WORKS_HISTORY_SIZE,
    YIT_MAX_WORKS_HISTORY_SIZE,
)
from .utils import (
    create_dict_from_yit_events,
    create_yit_maintenance_units,
    get_linestring_in_boundary,
    get_turku_boundary,
    get_yit_access_token,
    get_yit_contract,
    get_yit_event_types,
    get_yit_routes,
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

    def create_yit_maintenance_works(self, history_size=None):
        access_token = get_yit_access_token()
        create_yit_maintenance_units(access_token)
        contract = get_yit_contract(access_token)
        list_of_events = get_yit_event_types(access_token)
        event_name_mappings = create_dict_from_yit_events(list_of_events)
        routes = get_yit_routes(access_token, contract, history_size)
        ids_to_delete = list(
            MaintenanceUnit.objects.filter(provider=YIT).values_list("id", flat=True)
        )
        num_created = 0
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
            # Create linestring that is inside the boundary of Turku
            # and discard parts of the geometry if they are outside the boundary.
            geometry = get_linestring_in_boundary(geometry, TURKU_BOUNDARY)
            if not geometry:
                continue
            events = []
            original_event_names = []
            operations = route["operations"]
            for operation in operations:
                event_name = event_name_mappings[operation].lower()
                if event_name in EVENT_MAPPINGS:
                    for e in EVENT_MAPPINGS[event_name]:
                        # If mapping value is None, the event is not used.
                        if e:
                            events.append(e)
                            original_event_names.append(event_name_mappings[operation])
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

            obj, created = MaintenanceWork.objects.get_or_create(
                timestamp=route["startTime"],
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
            maintenance_unit__provider=YIT
        ).count()
        logger.info(f"Deleted {len(ids_to_delete)} obsolete Works for provider {YIT}")
        logger.info(
            f"Created {num_created} Works of total {num_works} Works for provider {YIT}."
        )
        return num_created

    def handle(self, *args, **options):
        super().__init__()
        MaintenanceWork.objects.filter(maintenance_unit__provider=YIT).delete()
        history_size = YIT_DEFAULT_WORKS_HISTORY_SIZE
        if options["history_size"]:
            history_size = int(options["history_size"][0])
            if history_size > YIT_MAX_WORKS_HISTORY_SIZE:
                error_msg = (
                    f"Max value for the history size is: {YIT_MAX_WORKS_HISTORY_SIZE}"
                )
                raise ValueError(error_msg)

        works_created = self.create_yit_maintenance_works(history_size=history_size)
        # In some unknown(erroneous server?) cases no data for works is availale. In that case we want to store
        # the previeus state of the precalculated geometry history data.
        if works_created > 0:
            precalculate_geometry_history(YIT)
        else:
            logger.warning(
                f"No works created for {YIT}, skipping geometry history population."
            )
        super().display_duration(YIT)
