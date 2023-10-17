import logging

from django import db
from django.core.management.base import BaseCommand

from environment_data.models import (
    Day,
    Hour,
    ImportState,
    Month,
    Parameter,
    Station,
    Week,
    Year,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    @db.transaction.atomic
    def handle(self, *args, **options):
        logger.info("Deleting all environment data...")
        logger.info(f"{Station.objects.all().delete()}")
        logger.info(f"{Parameter.objects.all().delete()}")
        logger.info(f"{Year.objects.all().delete()}")
        logger.info(f"{Month.objects.all().delete()}")
        logger.info(f"{Week.objects.all().delete()}")
        logger.info(f"{Day.objects.all().delete()}")
        logger.info(f"{Hour.objects.all().delete()}")
        logger.info(f"{ImportState.objects.all().delete()}")
        logger.info("Deleted all environment data.")
