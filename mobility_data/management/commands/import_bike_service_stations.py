import logging

from mobility_data.importers.bike_service_stations import (
    get_bike_service_station_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing bike service stations.")
        geojson_file = None
        if options["test_mode"]:
            geojson_file = options["test_mode"]

        objects = get_bike_service_station_objects(geojson_file=geojson_file)
        save_to_database(objects)
        logger.info(f"Imported {len(objects)} bike service stations.")
