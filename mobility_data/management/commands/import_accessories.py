import logging

from mobility_data.importers.accessories import (
    get_accessory_elements,
    get_accessory_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand
from ._utils import get_test_gdal_data_source

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing accessories...")
        data_source = None
        if options["test_mode"]:
            data_source = get_test_gdal_data_source(options["test_mode"])
        accessories = get_accessory_objects(data_source=data_source)
        for key, value in get_accessory_elements().items():
            objects = getattr(accessories, value["objects_field_name"], None)
            create_content_type_func = value["create_content_type_func"]
            content_type = value["content_type"]
            save_to_database(objects, create_content_type_func, content_type)
            logger.info(f"Imported {len(objects)} {key}.")
