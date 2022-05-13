import json
import logging
import os

from mobility_data.importers.gas_filling_station import (
    GAS_FILLING_STATIONS_URL,
    get_filtered_gas_filling_station_objects,
    save_to_database,
)
from mobility_data.models import ContentType

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing gas filling stations.")
        if options["test_mode"]:
            logger.info("Running gas filling station_importer in test mode.")
            f = open(
                os.getcwd()
                + "/"
                + ContentType._meta.app_label
                + "/tests/data/"
                + options["test_mode"],
                "r",
            )
            json_data = json.load(f)
            objects = get_filtered_gas_filling_station_objects(json_data=json_data)
        else:
            logger.info(
                "Fetching gas filling stations from: {}".format(
                    GAS_FILLING_STATIONS_URL
                )
            )
            objects = get_filtered_gas_filling_station_objects()
        save_to_database(objects)
