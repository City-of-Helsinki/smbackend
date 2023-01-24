import logging

from django.core.management import BaseCommand

from mobility_data.importers.foli_parkandride_stop import (
    FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME,
    FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME,
    get_objects,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        car_stops, bike_stops = get_objects()
        logger.info(
            f"Saved {save_to_database(car_stops, FOLI_PARKANDRIDE_CARS_STOP_CONTENT_TYPE_NAME)} "
            "Föli park and ride car stops to database"
        )
        logger.info(
            f"Saved {save_to_database(bike_stops, FOLI_PARKANDRIDE_BIKES_STOP_CONTENT_TYPE_NAME)} "
            "Föli park and ride bike stops to database"
        )
