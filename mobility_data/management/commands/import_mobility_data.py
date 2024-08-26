"""
Imports all mobility data sources.
"""

import logging

from django.core import management
from django.core.management import BaseCommand

from mobility_data.management.commands.import_wfs import (
    get_configured_cotent_type_names,
)

# Names of the mobility_data importers to be include when importing data.
importers = [
    "bicycle_stands",
    "culture_routes",
    "gas_filling_stations",
    "charging_stations",
    "bike_service_stations",
    "share_car_parking_places",
    "marinas",
    "disabled_and_no_staff_parkings",
    "loading_and_unloading_places",
    "lounaistieto_shapefiles",
    "foli_stops",
    "outdoor_gym_devices",
    "foli_parkandride_stops",
    "under_and_overpasses",
    "parking_garages",
]
# Read the content type names to be imported
wfs_content_type_names = get_configured_cotent_type_names()
logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing mobility data...")
        management.call_command("import_wfs", wfs_content_type_names)
        for importer in importers:
            management.call_command(f"import_{importer}")
