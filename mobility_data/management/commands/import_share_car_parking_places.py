import logging

from mobility_data.importers.share_car_parking_places import (
    get_car_share_parking_place_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing car share parking places.")
        geojson_file = None
        if options["test_mode"]:
            geojson_file = options["test_mode"]

        objects = get_car_share_parking_place_objects(geojson_file=geojson_file)
        save_to_database(objects)
        logger.info(f"Imported {len(objects)} char share parking places.")
