import logging

from django.core.management import BaseCommand

from mobility_data.importers.culture_routes import (
    get_routes,
    GROUP_CONTENT_TYPE_NAME,
    save_to_database,
)
from mobility_data.models import MobileUnitGroup

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
        delete_tables = options.get("delete", False)
        if delete_tables:
            MobileUnitGroup.objects.filter(
                group_type__type_name=GROUP_CONTENT_TYPE_NAME
            ).delete()
        routes = get_routes()
        routes_saved, routes_deleted, units_saved, units_deleted = save_to_database(
            routes, delete_tables=delete_tables
        )
        logger.info(
            "Fetched {} Culture Routes. Saved {} routes and deleted {} obsolete routes."
            " Saved {} units and deleted {} obsolete units".format(
                len(routes), routes_saved, routes_deleted, units_saved, units_deleted
            )
        )
