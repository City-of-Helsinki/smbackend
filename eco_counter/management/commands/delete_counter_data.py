import logging

from django import db
from django.core.management.base import BaseCommand

from eco_counter.constants import COUNTER_CHOICES_STR
from eco_counter.management.commands.utils import check_counters_argument
from eco_counter.models import ImportState, Station

logger = logging.getLogger("eco_counter")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--counters",
            type=str,
            nargs="+",
            default=False,
            help=f"Delete given counter data, choices are: {COUNTER_CHOICES_STR}.",
        )

    @db.transaction.atomic
    def handle(self, *args, **options):
        counters = options.get("counters", None)
        check_counters_argument(counters)
        if counters:
            for counter in counters:
                logger.info(f"Deleting counter data for {counter}")
                logger.info(
                    f"{Station.objects.filter(csv_data_source=counter).delete()}"
                )
                logger.info(
                    f"{ImportState.objects.filter(csv_data_source=counter).delete()}"
                )
                logger.info("Deleted counter data.")
