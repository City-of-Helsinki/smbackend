import logging

from mobility_data.importers.no_staff_parking import (
    get_no_staff_parking_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing no staff parkings.")
        objects = get_no_staff_parking_objects()
        save_to_database(objects)
        logger.info(f"Imorted {len(objects)} no staff parkings")
