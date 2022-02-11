import os
import json
import logging
from django.core.management import BaseCommand
from mobility_data.importers.culture_routes import (
    get_routes,
    save_to_database,
)
from mobility_data.models import ContentType

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            default=False,
            help="Deletes Culture Routes before importing. ",
        )

    def handle(self, *args, **options):
        logger.info("Importing culture routes...")
        routes = get_routes()
        delete_tables = False
        if options["delete"]:
            delete_tables = True
        num_saved = save_to_database(routes, delete_tables=delete_tables)
        logger.info(
            "Fetched {} Culture Routes and saved {} new Culture Routes to database.".format(
                len(routes), num_saved
            )
        )
