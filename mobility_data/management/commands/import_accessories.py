import logging

from django.core.management import BaseCommand

from mobility_data.importers.accessories import (
    get_accessory_elements,
    get_accessory_objects,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing accessories...")
        accessories = get_accessory_objects()
        for key, value in get_accessory_elements().items():
            objects = getattr(accessories, value["objects_field_name"], None)
            create_content_type_func = value["create_content_type_func"]
            content_type = value["content_type"]
            save_to_database(objects, create_content_type_func, content_type)
            logger.info(f"Imported {len(objects)} {key}.")
