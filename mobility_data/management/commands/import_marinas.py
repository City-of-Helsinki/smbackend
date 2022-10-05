import logging

from mobility_data.importers.marinas import (
    import_guest_marina_and_boat_parking,
    import_marinas,
)

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info(f"Imported {import_marinas()} marinas.")
        import_guest_marina_and_boat_parking()
        logger.info("Imported guest marina and boat parking.")
