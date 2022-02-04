import xml.etree.ElementTree as ET
import logging
from django.core.management import BaseCommand
from django.conf import settings
from mobility_data.importers.bicycle_stands import (
    get_bicycle_stand_objects,
    save_to_database,
    BICYCLE_STANDS_URL,
)
from mobility_data.models import ContentType

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--test-mode",
            nargs="+",
            default=False,
            help="Run script in test mode.",
        )

    def handle(self, *args, **options):
        logger.info("Importing bicycle stands.")
        if options["test_mode"]:
            logger.info("Running bicycle stand importer in test mode.")
            path = f"{settings.BASE_DIR}/{ContentType._meta.app_label}/tests/data/"
            filename = options["test_mode"]
            xml_data = None
            with open(path + filename, "r") as xml_file:
                xml_data = ET.parse(xml_file)
            objects = get_bicycle_stand_objects(xml_data=xml_data)
        else:
            logger.info("Fetching bicycle stands from: {}".format(BICYCLE_STANDS_URL))
            objects = get_bicycle_stand_objects()
        save_to_database(objects)
