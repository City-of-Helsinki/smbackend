import logging

from street_maintenance.models import MaintenanceUnit

from .base_import_command import BaseImportCommand
from .constants import (
    INFRAROAD,
    INFRAROAD_DEFAULT_WORKS_FETCH_SIZE,
    INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE,
)
from .utils import (
    create_maintenance_units,
    create_maintenance_works,
    precalculate_geometry_history,
)

logger = logging.getLogger("street_maintenance")


class Command(BaseImportCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--fetch-size",
            type=int,
            nargs="+",
            default=False,
            help=(
                "Max number of location history items to fetch per unit."
                + "Default {INFRAROAD_DEFAULT_WORKS_FETCH_SIZE}."
            ),
        )
        parser.add_argument(
            "--history-size",
            type=int,
            nargs="+",
            default=False,
            help=(
                "History size in days."
                + "Default {INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE}."
            ),
        )

    def handle(self, *args, **options):
        super().__init__()
        MaintenanceUnit.objects.filter(provider=INFRAROAD).delete()
        if options["history_size"]:
            history_size = options["history_size"][0]
        else:
            history_size = INFRAROAD_DEFAULT_WORKS_HISTORY_SIZE

        if options["fetch_size"]:
            fetch_size = options["fetch_size"][0]
        else:
            fetch_size = INFRAROAD_DEFAULT_WORKS_FETCH_SIZE
        create_maintenance_units(INFRAROAD)
        num_works_created = create_maintenance_works(
            INFRAROAD, history_size, fetch_size
        )
        if num_works_created > 0:
            precalculate_geometry_history(INFRAROAD)
        else:
            logger.warning(
                f"No works created for {INFRAROAD}, skipping geometry history population."
            )

        super().display_duration(INFRAROAD)
