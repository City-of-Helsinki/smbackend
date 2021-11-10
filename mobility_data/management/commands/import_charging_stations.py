import os
import logging
import json
from django.core.management import BaseCommand
from mobility_data.models import ContentType
from mobility_data.importers.charging_stations import(
    get_filtered_charging_station_objects,
    save_to_database,
    CHARGING_STATIONS_URL1
)
logger = logging.getLogger("mobility_data")
    
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(            
            "--test-mode",             
            nargs="+",
            default=False,
            help="Run script in test mode. ",
        )       
    
    def handle(self, *args, **options):
        logger.info("Importing charging stations.")
        if options["test_mode"]:
            logger.info("Running charging_station_importer in test mode.")
            f = open(os.getcwd()+"/"+ContentType._meta.app_label+"/tests/data/"+options["test_mode"], "r")
            json_data = json.load(f)
            objects = get_filtered_charging_station_objects(json_data=json_data)       
        else:
            logger.info("Fetching charging stations from: {}"\
                .format(CHARGING_STATIONS_URL1))
            objects = get_filtered_charging_station_objects()
        save_to_database(objects)