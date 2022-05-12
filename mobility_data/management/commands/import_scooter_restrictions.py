import logging

from django.core.management import BaseCommand
from mobility_data.importers.scooter_restrictions import (
    get_datasource_layer,
    get_restriction_objects,
    get_scooter_restriction_elements,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing Scooter restrictions.")
        for key, value in get_scooter_restriction_elements().items():
            layer = get_datasource_layer(value["url"])
            objects = get_restriction_objects(layer)
            save_to_database(
                objects, value["content_type_create_func"], value["content_type"]
            )
            logger.info(f"Imported {len(objects)} {key} objects.")
