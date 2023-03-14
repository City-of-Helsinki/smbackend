import logging

from mobility_data.importers.marinas import (
    BOAT_PARKING_CONTENT_TYPE_NAME,
    get_boat_parkings,
    get_guest_marinas,
    get_marinas,
    GUEST_MARINA_CONTENT_TYPE_NAME,
    MARINA_CONTENT_TYPE_NAME,
)
from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
    save_to_database,
)

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        objects = get_marinas()
        content_type = get_or_create_content_type_from_config(MARINA_CONTENT_TYPE_NAME)
        num_ceated, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)

        objects = get_boat_parkings()
        content_type = get_or_create_content_type_from_config(
            BOAT_PARKING_CONTENT_TYPE_NAME
        )
        num_ceated, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)

        objects = get_guest_marinas()
        content_type = get_or_create_content_type_from_config(
            GUEST_MARINA_CONTENT_TYPE_NAME
        )
        num_ceated, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)
