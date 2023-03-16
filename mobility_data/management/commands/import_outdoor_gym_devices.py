import logging

from mobility_data.importers.outdoor_gym_devices import (
    CONTENT_TYPE_NAME,
    get_oudoor_gym_devices,
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
        objects = get_oudoor_gym_devices()
        content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
        num_ceated, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)
