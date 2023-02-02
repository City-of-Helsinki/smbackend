import logging

from django.core.management import BaseCommand

from mobility_data.importers.parking_machines import (
    get_parking_machine_objects,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        objects = get_parking_machine_objects()
        save_to_database(objects)
        logger.info(f"Saved {len(objects)} parking machines to database.")
