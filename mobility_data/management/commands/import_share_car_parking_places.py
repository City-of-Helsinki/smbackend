import logging

from django.core.management import BaseCommand

from mobility_data.importers.share_car_parking_places import (
    CONTENT_TYPE_NAME,
    get_car_share_parking_place_objects,
)
from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing car share parking places.")
        objects = get_car_share_parking_place_objects()
        content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
        num_created, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_created, num_deleted)
