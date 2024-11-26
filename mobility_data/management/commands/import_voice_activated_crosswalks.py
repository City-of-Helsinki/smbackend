import logging

from django.core.management import BaseCommand

from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
    save_to_database,
)
from mobility_data.importers.voice_activated_crosswalks import (
    CONTENT_TYPE_NAME,
    get_voice_activated_crosswalks,
)

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        objects = get_voice_activated_crosswalks()
        content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
        num_created, num_deleted = save_to_database(objects, content_type)
        log_imported_message(logger, content_type, num_created, num_deleted)
