import logging

from django.core.management import BaseCommand

from mobility_data.importers.under_and_overpasses import (
    get_under_and_overpass_objects,
    OVERPASS_CONTENT_TYPE_NAME,
    UNDERPASS_CONTENT_TYPE_NAME,
)
from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
    save_to_database,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        underpass_objects, overpass_objects = get_under_and_overpass_objects()
        content_type = get_or_create_content_type_from_config(
            UNDERPASS_CONTENT_TYPE_NAME
        )
        num_ceated, num_deleted = save_to_database(underpass_objects, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)
        content_type = get_or_create_content_type_from_config(
            OVERPASS_CONTENT_TYPE_NAME
        )
        num_ceated, num_deleted = save_to_database(overpass_objects, content_type)
        log_imported_message(logger, content_type, num_ceated, num_deleted)
