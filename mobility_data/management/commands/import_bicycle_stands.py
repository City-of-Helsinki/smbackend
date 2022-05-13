import logging

from mobility_data.importers.bicycle_stands import (
    BICYCLE_STANDS_URL,
    get_bicycle_stand_objects,
    save_to_database,
)

from ._base_import_command import BaseImportCommand
from ._utils import get_test_gdal_data_source

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing bicycle stands.")
        if options["test_mode"]:
            logger.info("Running bicycle stand importer in test mode.")
            file_name = options["test_mode"]
            data_source = None
            ds = get_test_gdal_data_source(file_name)

            if file_name.endswith("gml"):
                data_source = ("gml", ds)
            elif file_name.endswith("geojson"):
                data_source = ("geojson", ds)

            objects = get_bicycle_stand_objects(data_source=data_source)
        else:
            logger.info("Fetching bicycle stands from: {}".format(BICYCLE_STANDS_URL))
            objects = get_bicycle_stand_objects()
        save_to_database(objects)
