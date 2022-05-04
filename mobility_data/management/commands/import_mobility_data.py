"""
Main importer for mobility data sources.
"""
import logging

from django.core import management
from django.core.management import BaseCommand

# Names of the mobility_data importers to be include when importing data.
importers = [
    "culture_routes",
    "gas_filling_stations",
    "bicycle_stands",
    "payment_zones",
    "scooter_restrictions",
]
logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing mobility data...")
        for importer in importers:
            management.call_command(f"import_{importer}")
