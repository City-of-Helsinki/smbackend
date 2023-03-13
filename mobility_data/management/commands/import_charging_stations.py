import logging

from mobility_data.importers.charging_stations import (
    CONTENT_TYPE_NAME,
    get_charging_station_objects,
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
        logger.info("Importing charging stations...")
        csv_file = None
        if options["test_mode"]:
            logger.info("Running charging_station_importer in test mode.")
            csv_file = options["test_mode"]
        objects = get_charging_station_objects(csv_file=csv_file)
        content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
        num_created, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_created, num_deleted)
