import os
import json
import logging
from django.core.management import BaseCommand

from mobility_data.importers.bicycle_stands import(
    get_bicycle_stand_objects,
    save_to_database,
    BICYCLE_STANDS_URL,
)
from mobility_data.models import ContentType
logger = logging.getLogger("mobility_data")

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(            
            "--test-mode",             
            nargs="+",
            default=False,
            help="Run script in test mode.",
        )       
    
    def handle(self, *args, **options):
        logger.info("Importing bicycle stands.")
        if options["test_mode"]:
            logger.info("Running bicycle stand importer in test mode.")
            f = open(os.getcwd()+"/"+ContentType._meta.app_label+"/tests/data/"+options["test_mode"], "r")
            json_data = json.load(f)
            #objects = get_filtered_gas_filling_station_objects(json_data=json_data)       
        else:
            logger.info("Fetching gas filling stations from: {}"\
                .format(BICYCLE_STANDS_URL))            
            objects = get_bicycle_stand_objects()       
        save_to_database(objects)