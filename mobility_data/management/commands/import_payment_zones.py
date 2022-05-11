import logging

from mobility_data.importers.payment_zones import (
    get_payment_zone_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand
from ._utils import get_test_gdal_data_source

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing payment zones.")
        if options["test_mode"]:
            logger.info("Running payment_zones importer in test mode.")
            data_source = get_test_gdal_data_source(options["test_mode"])
            objects = get_payment_zone_objects(data_source=data_source)
        else:
            objects = get_payment_zone_objects()
        save_to_database(objects)
        logger.info(f"Saved {len(objects)} payment zones.")
