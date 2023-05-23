import json
import logging
import os
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from django.conf import settings
from django.core.management import BaseCommand

from eco_counter.constants import (
    INDEX_COLUMN_NAME,
    TELRAAM_COUNTER_API_TIME_FORMAT,
    TELRAAM_COUNTER_CSV_FILE,
    TELRAAM_COUNTER_CSV_FILE_PATH,
    TELRAAM_COUNTER_START_MONTH,
    TELRAAM_COUNTER_START_YEAR,
    TELRAAM_COUNTER_TRAFFIC_URL,
    TELRAAM_CSV,
)
from eco_counter.management.commands.utils import get_telraam_cameras
from eco_counter.models import ImportState

LEVEL = "instances"  # instance per individual can
FORMAT = "per-hour"

TOKEN = settings.TELRAAM_TOKEN
assert TOKEN
logger = logging.getLogger("eco_counter")

HEAVY = "heavy"
VEHICLE_TYPES = {
    "pedestrian": "J",
    "bike": "P",
    "car": "A",
    HEAVY: "A",  # Is added to car column
}
LEFT = "lft"
RIGHT = "rgt"
DIRECTIONS = [LEFT, RIGHT]


def get_mappings(station_name, direction=True):
    """
    return mappings:
    e.g.,
    "pedestrian_lgt": "station_name KP"
    """
    dir1, dir2 = "K", "P"
    if not direction:
        dir1, dir2 = dir2, dir1
    dirs = {
        LEFT: dir1,
        RIGHT: dir2,
    }
    column_mappings = {}
    for veh in VEHICLE_TYPES.items():
        for dir in DIRECTIONS:
            key = f"{veh[0]}_{dir}"
            value = f"{veh[1]}{dirs[dir]}"
            column_mappings[key] = value
    mappings = {}
    for field in column_mappings.keys():
        mappings[field] = f"{station_name} {column_mappings[field]}"
    return mappings


def fetch_traffic_report(from_date: str, end_date: str, camera_id: str):
    headers = {
        "X-Api-Key": TOKEN,
        "Content-Type": "application/json",
    }
    data = {
        "level": LEVEL,  # segments
        "format": FORMAT,
        "id": camera_id,
        "time_start": from_date,
        "time_end": end_date,
    }
    response = requests.post(
        TELRAAM_COUNTER_TRAFFIC_URL, headers=headers, data=json.dumps(data)
    )
    report = response.json().get("report", [])
    print(len(report))
    return report


def get_delta_hours(from_date: datetime, end_date: datetime) -> datetime:
    delta = end_date - from_date
    delta_hours = int(round(delta.total_seconds() / 3600))
    return delta_hours


def get_day_data(
    day_date: date, camera_id: str, check_delta_hours: bool = True
) -> list:
    from_datetime = datetime(day_date.year, day_date.month, day_date.day, 0, 0, 0)
    from_datetime_str = from_datetime.strftime(TELRAAM_COUNTER_API_TIME_FORMAT)
    end_datetime = (
        datetime(day_date.year, day_date.month, day_date.day)
        + timedelta(hours=23)
        + timedelta(minutes=59)
    )
    end_datetime_str = end_datetime.strftime(TELRAAM_COUNTER_API_TIME_FORMAT)
    report = fetch_traffic_report(from_datetime_str, end_datetime_str, camera_id)

    delta_hours = get_delta_hours(from_datetime, end_datetime)
    logger.info(f"Trying to import {delta_hours} hours for camera {camera_id}.")
    if not report:
        logger.warning("No report found, populating with empty dicts")
        report = [{} for a in range(delta_hours)]
    else:
        logger.info(f"Imorted report with {len(report)} elements")
    delta_hours = len(report)
    if check_delta_hours and delta_hours != 24:
        dif = 24 - delta_hours
        logger.warning(
            f"Fetched report with delta_hours not equal to 24, appending missing {dif} elements empty dicts"
        )
        report += [{} for a in range(dif)]

    res = []
    start_date = from_datetime
    for item in report:
        d = {}
        d["date"] = datetime.strftime(start_date, TELRAAM_COUNTER_API_TIME_FORMAT)
        for veh in VEHICLE_TYPES.keys():
            for dir in DIRECTIONS:
                key = f"{veh}_{dir}"
                val = int(round(item.get(key, 0)))
                d[key] = val
        res.append(d)
        start_date += timedelta(hours=1)
    return res, delta_hours


def save_dataframe():
    if not os.path.exists(TELRAAM_COUNTER_CSV_FILE_PATH):
        os.makedirs(TELRAAM_COUNTER_CSV_FILE_PATH)
        ImportState.objects.filter(csv_data_source=TELRAAM_CSV).delete()
        import_state = ImportState.objects.create(
            csv_data_source=TELRAAM_CSV,
            current_year_number=TELRAAM_COUNTER_START_YEAR,
            current_month_number=TELRAAM_COUNTER_START_MONTH,
            current_day_number=1,
        )
    else:
        import_state = ImportState.objects.filter(csv_data_source=TELRAAM_CSV).first()

    from_date = date(
        import_state.current_year_number,
        import_state.current_month_number,
        import_state.current_day_number,
    )
    date_today = date.today()
    logger.info(f"Fetching Telraam data from {str(from_date)} to {str(date_today)}")

    cameras = get_telraam_cameras()
    for camera in cameras:
        start_date = from_date
        while start_date <= date_today:
            report, delta_hours = get_day_data(start_date, camera["instance_id"])
            mappings = get_mappings(camera["mac"])
            columns = {}
            columns[INDEX_COLUMN_NAME] = []
            for hour in range(delta_hours):
                columns[INDEX_COLUMN_NAME].append(report[hour]["date"])
                for mapping in mappings.items():
                    # key is the name of the column, e.g., name_ak
                    key = mapping[1]
                    value_key = mapping[0]
                    values_list = columns.get(key, [])
                    if HEAVY in value_key:
                        # add heavy values to car column, as the mapping is same.
                        values_list[-1] += report[hour][value_key]
                    else:
                        values_list.append(report[hour][value_key])
                    columns[key] = values_list
            df = pd.DataFrame(data=columns, index=columns[INDEX_COLUMN_NAME])
            df = df.drop(columns=[INDEX_COLUMN_NAME], axis=1)
            df.index.rename(INDEX_COLUMN_NAME, inplace=True)
            df = df.fillna(0)
            df = df.astype(int)

            csv_file = TELRAAM_COUNTER_CSV_FILE.format(
                id=camera["mac"],
                day=start_date.day,
                month=start_date.month,
                year=start_date.year,
            )
            if start_date == date_today:
                # Remove latest csv, as it might not be populated until the end of day
                if os.path.exists(csv_file):
                    os.remove(csv_file)
            if not os.path.exists(csv_file):
                df.to_csv(csv_file)
            start_date += timedelta(days=1)

    start_date -= timedelta(days=1)
    import_state.current_year_number = start_date.year
    import_state.current_month_number = start_date.month
    import_state.current_day_number = start_date.day
    import_state.save()
    logger.info(f"Telraam data imported until {str(start_date)}")


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing Telraam data...")
        save_dataframe()
