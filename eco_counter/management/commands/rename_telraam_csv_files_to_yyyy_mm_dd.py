import logging
import os

from django.core.management import BaseCommand

from eco_counter.constants import (
    TELRAAM_COUNTER_CSV_FILE,
    TELRAAM_COUNTER_CSV_FILE_PATH,
)

logger = logging.getLogger("eco_counter")

TELRAAM_COUNTER_OLD_CSV_FILE = (
    TELRAAM_COUNTER_CSV_FILE_PATH + "telraam_data_{mac}_{year}_{month}_{day}.csv"
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Renaming Telraam CSV files...")
        num_renamed = 0
        for filename in os.listdir(TELRAAM_COUNTER_CSV_FILE_PATH):
            # Check if filename end with 'YYYY.csv' and must be renamed
            if len(filename.split("_")[-1]) == 8:
                _, _, mac, day, month, year = filename.split("_")
                year = year.split(".")[0]
                os.rename(
                    os.path.join(TELRAAM_COUNTER_CSV_FILE_PATH, filename),
                    os.path.join(
                        TELRAAM_COUNTER_CSV_FILE_PATH,
                        TELRAAM_COUNTER_CSV_FILE.format(
                            mac=mac, year=year, month=month, day=day
                        ),
                    ),
                )
                num_renamed += 1
        logger.info(f"Renamed {num_renamed} Telraam CSV files.")
