import logging

from django.core.management import BaseCommand

from mobility_data.importers.payment_zones import (
    get_payment_zone_objects,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing payment zones.")
        objects = get_payment_zone_objects()
        save_to_database(objects)
        logger.info(f"Saved {len(objects)} payment zones.")
