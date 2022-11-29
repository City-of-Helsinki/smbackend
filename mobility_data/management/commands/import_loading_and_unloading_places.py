import logging

from mobility_data.importers.loading_unloading_places import (
    get_loading_and_unloading_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing loading and unloading places.")
        geojson_file = None
        if options["test_mode"]:
            geojson_file = options["test_mode"]
        objects = get_loading_and_unloading_objects(geojson_file=geojson_file)
        save_to_database(objects)
        logger.info(f"Imported {len(objects)} loading and unloading places.")
