import logging

from mobility_data.importers.foli_stops import get_foli_stops, save_to_database

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing Föli stops")
        objects = get_foli_stops()
        save_to_database(objects)
