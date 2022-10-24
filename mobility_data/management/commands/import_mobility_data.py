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
    "charging_stations",
    "bicycle_stands",
    "payment_zones",
    "speed_limit_zones",
    "scooter_restrictions",
    "accessories",
    "bike_service_stations",
    "share_car_parking_places",
    "bicycle_networks",
    "marinas",
    "disabled_and_no_staff_parkings",
    "loading_and_unloading_places",
    "lounaistieto_shapefiles",
]
logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing mobility data...")
        for importer in importers:
            management.call_command(f"import_{importer}")
