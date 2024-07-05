import logging

from django import db
from django.core.management.base import BaseCommand

from eco_counter.models import (
    Day,
    DayData,
    HourData,
    ImportState,
    Month,
    MonthData,
    Station,
    Week,
    WeekData,
    Year,
    YearData,
)

logger = logging.getLogger("eco_counter")

MODELS_TO_DELETE = [
    ImportState,
    Station,
    Year,
    Month,
    Week,
    Day,
    YearData,
    MonthData,
    WeekData,
    DayData,
    HourData,
]


class Command(BaseCommand):

    @db.transaction.atomic
    def handle(self, *args, **options):
        for model in MODELS_TO_DELETE:
            model.objects.all().delete()
