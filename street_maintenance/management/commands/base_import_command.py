import logging
from datetime import datetime

from django.core.management import BaseCommand

logger = logging.getLogger("street_maintenance")


class BaseImportCommand(BaseCommand):
    def __init__(self):
        self.start_time = datetime.now()

    def display_duration(self, provider):
        end_time = datetime.now()
        duration = end_time - self.start_time
        logger.info(f"Imported {provider} street maintenance history in: {duration}")
