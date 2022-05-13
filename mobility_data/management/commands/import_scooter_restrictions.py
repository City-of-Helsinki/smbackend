import logging

from mobility_data.importers.scooter_restrictions import (
    get_datasource_layer,
    get_restriction_objects,
    get_scooter_restriction_elements,
    save_to_database,
)

from ._base_import_command import BaseImportCommand
from ._utils import get_test_gdal_data_source

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing Scooter restrictions.")
        for key, value in get_scooter_restriction_elements().items():
            if options["test_mode"]:
                data_source = get_test_gdal_data_source(value["test_data"])
                layer = data_source[0]
            else:
                layer = get_datasource_layer(value["url"])
            objects = get_restriction_objects(layer)
            save_to_database(
                objects, value["content_type_create_func"], value["content_type"]
            )
            logger.info(f"Imported {len(objects)} {key} objects.")
