import logging

from mobility_data.importers.disabled_and_no_staff_parking import (
    get_no_staff_parking_objects,
    save_to_database,
)
from mobility_data.models import ContentType

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing disabled and no staff parkings.")
        geojson_file = None
        if options["test_mode"]:
            geojson_file = options["test_mode"]
        objects = get_no_staff_parking_objects(geojson_file=geojson_file)
        save_to_database(objects)
        num_no_staff_parkings = len(
            [x for x in objects if x.content_type == ContentType.NO_STAFF_PARKING]
        )
        num_disabled_parkings = len(
            [x for x in objects if x.content_type == ContentType.DISABLED_PARKING]
        )
        logger.info(f"Imorted {num_no_staff_parkings} no staff parkings")
        logger.info(f"Imorted {num_disabled_parkings} disabled parkings")
