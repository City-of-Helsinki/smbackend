import logging

from django.core.management import BaseCommand

from mobility_data.importers.speed_limits import (
    get_speed_limit_objects,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing speed limit.")
        objects = get_speed_limit_objects()
        save_to_database(objects)
        logger.info(f"Imported {len(objects)} speed limit zones.")
