import logging

from django.core.management import BaseCommand

from mobility_data.importers.foli_stops import get_foli_stops, save_to_database

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing Föli stops")
        objects = get_foli_stops()
        save_to_database(objects)
