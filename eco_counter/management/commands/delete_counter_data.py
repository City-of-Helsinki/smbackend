import logging

from django import db
from django.core.management.base import BaseCommand

from eco_counter.constants import COUNTER_CHOICES_STR
from eco_counter.management.commands.utils import check_counters_argument
from eco_counter.models import Day, ImportState, Month, Station, Week, Year

logger = logging.getLogger("eco_counter")


def delete_if_no_relations(items):
    # If model does not have related rows, delete it.
    # Cleans useless Year, Month, Week, Day rows.
    for item in items:
        model = item[0]
        related_name = item[1]
        for row in model.objects.all():
            if not getattr(row, related_name).exists():
                row.delete()


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
        items = [
            (Year, "year_data"),
            (Month, "month_data"),
            (Week, "week_data"),
            (Day, "day_data"),
        ]
        delete_if_no_relations(items)
