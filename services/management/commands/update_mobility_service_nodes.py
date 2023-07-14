import logging
from time import time

from django.core.management.base import BaseCommand

from .services_import.services import update_mobility_service_nodes

logger = logging.getLogger("services.management")


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logger.info("Updating mobility service nodes...")
        start_time = time()
        service_node_count = update_mobility_service_nodes()
        logger.info(
            f"{service_node_count} mobility service nodes updated "
            f"in {time() - start_time:.0f} seconds."
        )
