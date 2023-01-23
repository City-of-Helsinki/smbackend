import logging

from mobility_data.importers.outdoor_gym_devices import save_outdoor_gym_devices

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info(f"Imported {save_outdoor_gym_devices()} outdoor gym devices")
