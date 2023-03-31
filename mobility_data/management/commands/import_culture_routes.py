import logging

from django.core.management import BaseCommand

from mobility_data.importers.culture_routes import get_routes, save_to_database

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
        delete_tables = options.get("delete", False)
        routes_saved, routes_deleted, units_saved, units_deleted = save_to_database(
            routes, delete_tables=delete_tables
        )
        logger.info(
            "Fetched {} Culture Routes. Saved {} routes and deleted {} obsolete routes."
            " Saved {} units and deleted {} obsolete units".format(
                len(routes), routes_saved, routes_deleted, units_saved, units_deleted
            )
        )
