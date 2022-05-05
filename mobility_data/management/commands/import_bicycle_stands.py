import logging

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.core.management import BaseCommand

from mobility_data.importers.bicycle_stands import (
    BICYCLE_STANDS_URL,
    get_bicycle_stand_objects,
    save_to_database,
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
            data_source = None
            ds = DataSource(path + filename)

            if filename.endswith("gml"):
                data_source = ("gml", ds)
            elif filename.endswith("geojson"):
                data_source = ("geojson", ds)

            objects = get_bicycle_stand_objects(data_source=data_source)
        else:
            logger.info("Fetching bicycle stands from: {}".format(BICYCLE_STANDS_URL))
            objects = get_bicycle_stand_objects()
        save_to_database(objects)
