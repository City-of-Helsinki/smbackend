import logging

from django.core.management import BaseCommand

from mobility_data.importers.foli_parkandride_stop import (
    FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME,
    FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME,
    get_parkandride_bike_stop_objects,
    get_parkandride_car_stop_objects,
)
from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        car_stops = get_parkandride_car_stop_objects()
        content_type = get_or_create_content_type_from_config(
            FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME
        )
        num_ceated, num_deleted = save_to_database(car_stops, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)
        content_type = get_or_create_content_type_from_config(
            FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME
        )
        bike_stops = get_parkandride_bike_stop_objects()
        num_ceated, num_deleted = save_to_database(bike_stops, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)
