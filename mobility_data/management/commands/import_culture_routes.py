import os
import json
import logging
from django.core.management import BaseCommand
from mobility_data.importers.culture_routes import(
    get_routes,
    save_to_database,
)   
from mobility_data.models import ContentType
logger = logging.getLogger("mobility_data")

class Command(BaseCommand):  
    
    def handle(self, *args, **options):
        logger.info("Importing culture routes...")         
        routes = get_routes()
        save_to_database(routes)
        logger.info("Saved {} culture routes to database.".format(len(routes)))
        