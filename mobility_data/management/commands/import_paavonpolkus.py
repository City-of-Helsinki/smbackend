import logging

from mobility_data.importers.paavonpolkus import import_paavonpolkus

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info(f"Imported {import_paavonpolkus()} Paavonpolkua.")
