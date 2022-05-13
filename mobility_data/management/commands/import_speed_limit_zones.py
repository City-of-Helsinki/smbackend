import logging

from mobility_data.importers.speed_limits import (
    get_speed_limit_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand
from ._utils import get_test_gdal_data_source

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing speed limit.")
        if options["test_mode"]:
            logger.info("Running speed_limit_zones importer in test mode.")
            data_source = get_test_gdal_data_source(options["test_mode"])
            objects = get_speed_limit_objects(data_source=data_source)
        else:
            objects = get_speed_limit_objects()
        save_to_database(objects)
        logger.info(f"Imported {len(objects)} speed limit zones.")
