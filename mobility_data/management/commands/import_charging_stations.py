import logging
from mobility_data.importers.charging_stations import (
    get_charging_station_objects,
    save_to_database,
)
from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing charging stations...")
        csv_file = None
        if options["test_mode"]:
            logger.info("Running charging_station_importer in test mode.")
            csv_file = options["test_mode"]
        objects = get_charging_station_objects(csv_file=csv_file)
        save_to_database(objects)
