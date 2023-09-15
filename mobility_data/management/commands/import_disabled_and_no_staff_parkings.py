import logging

from django.core.management import BaseCommand

from mobility_data.importers.disabled_and_no_staff_parking import (
    DISABLED_PARKING_CONTENT_TYPE_NAME,
    get_no_staff_parking_objects,
    NO_STAFF_PARKING_CONTENT_TYPE_NAME,
)
from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing disabled and no staff parkings.")
        (
            no_stuff_parking_objects,
            disabled_parking_objects,
        ) = get_no_staff_parking_objects()
        content_type = get_or_create_content_type_from_config(
            NO_STAFF_PARKING_CONTENT_TYPE_NAME
        )
        num_created, num_deleted = save_to_database(
            no_stuff_parking_objects, content_type
        )
        log_imported_message(logger, content_type, num_created, num_deleted)
        content_type = get_or_create_content_type_from_config(
            DISABLED_PARKING_CONTENT_TYPE_NAME
        )
        num_created, num_deleted = save_to_database(
            disabled_parking_objects, content_type
        )
        log_imported_message(logger, content_type, num_created, num_deleted)
