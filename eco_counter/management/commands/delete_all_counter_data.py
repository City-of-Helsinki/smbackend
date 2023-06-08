import logging

from django import db
from django.core.management.base import BaseCommand

from eco_counter.models import ImportState, Station

logger = logging.getLogger("eco_counter")


class Command(BaseCommand):
    @db.transaction.atomic
    def handle(self, *args, **options):
        logger.info("Deleting all counter data...")
        logger.info(f"{Station.objects.all().delete()}")
        logger.info(f"{ImportState.objects.all().delete()}")
        logger.info("Deleted all counter data.")
