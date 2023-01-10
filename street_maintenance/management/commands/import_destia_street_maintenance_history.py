import logging

from street_maintenance.models import MaintenanceUnit

from .base_import_command import BaseImportCommand
from .constants import (
    DESTIA,
    DESTIA_DEFAULT_WORKS_FETCH_SIZE,
    DESTIA_DEFAULT_WORKS_HISTORY_SIZE,
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
                + "Default {DESTIA_DEFAULT_WORKS_FETCH_SIZE}."
            ),
        )
        parser.add_argument(
            "--history-size",
            type=int,
            nargs="+",
            default=False,
            help=(
                "History size in days." + "Default {DESTIA_DEFAULT_WORKS_HISTORY_SIZE}."
            ),
        )

    def handle(self, *args, **options):
        super().__init__()
        MaintenanceUnit.objects.filter(provider=DESTIA).delete()
        if options["history_size"]:
            history_size = options["history_size"][0]
        else:
            history_size = DESTIA_DEFAULT_WORKS_HISTORY_SIZE

        if options["fetch_size"]:
            fetch_size = options["fetch_size"][0]
        else:
            fetch_size = DESTIA_DEFAULT_WORKS_FETCH_SIZE
        create_maintenance_units(DESTIA)
        create_maintenance_works(DESTIA, history_size, fetch_size)
        precalculate_geometry_history(DESTIA)
        super().display_duration(DESTIA)
