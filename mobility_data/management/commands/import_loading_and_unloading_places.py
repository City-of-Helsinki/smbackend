import logging

from mobility_data.importers.loading_unloading_places import (
    CONTENT_TYPE_NAME,
    get_loading_and_unloading_objects,
)
from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
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
        content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
        num_ceated, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)
