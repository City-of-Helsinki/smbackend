import json
import logging
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from django.conf import settings
from django.core.management import BaseCommand

from eco_counter.constants import (
    TELRAAM_COUNTER_START_MONTH,
    TELRAAM_COUNTER_START_YEAR,
    TELRAAM_CSV_FILE_NAME,
)
from eco_counter.management.commands.utils import get_telraam_cameras
from mobility_data.importers.utils import get_root_dir

TELRAAM_API_BASE_URL = "https://telraam-api.net"
ALIVE_URL = f"{TELRAAM_API_BASE_URL}/v1"
# Maximum 3 months at a time
TRAFFIC_URL = f"{TELRAAM_API_BASE_URL}/v1/reports/traffic"
AVAILABLE_CAMERAS_URL = f"{TELRAAM_API_BASE_URL}/v1/cameras"
INDEX_COLUMN_NAME = "startTime"
LEVEL = "instances"  # instance per individual can
FORMAT = "per-hour"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATA_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

TOKEN = settings.TELRAAM_TOKEN
assert TOKEN
csv_file = f"{get_root_dir()}/media/{TELRAAM_CSV_FILE_NAME}"
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
    response = requests.post(TRAFFIC_URL, headers=headers, data=json.dumps(data))
    return response.json().get("report", [])


def get_delta_hours(from_date: datetime, end_date: datetime) -> datetime:
    delta = end_date - from_date
    delta_hours = int(round(delta.total_seconds() / 3600))
    return delta_hours


def get_hourly_data(from_date, end_date, camera_id):
    report = fetch_traffic_report(from_date, end_date, camera_id)
    from_date = datetime.strptime(from_date, TIME_FORMAT)
    end_date = datetime.strptime(end_date, TIME_FORMAT)
    delta_hours = get_delta_hours(from_date, end_date)
    logger.info(f"Trying to import {delta_hours} hours for camera {camera_id}.")
    if not report:
        report = [{} for a in range(delta_hours)]

    delta_hours = len(report)
    res = []
    start_date = from_date
    for item in report:
        d = {}
        d["date"] = datetime.strftime(start_date, TIME_FORMAT)
        for veh in VEHICLE_TYPES.keys():
            for dir in DIRECTIONS:
                key = f"{veh}_{dir}"
                val = int(round(item.get(key, 0)))
                d[key] = val
        res.append(d)
        start_date += timedelta(hours=1)
    return res, delta_hours


def save_dataframe():
    try:
        df = pd.read_csv(csv_file, index_col=INDEX_COLUMN_NAME)
        from_date = df.iloc[-1].name
        logger.info(f"Found Telraam data until {from_date} in csv file.")
        from_date = datetime.strptime(from_date, TIME_FORMAT) + timedelta(hours=1)
        from_date = datetime.strftime(from_date, TIME_FORMAT)
    except Exception:
        logger.info("Creating new empty Pandas DataFrame")
        df = pd.DataFrame()
        from_date = date(TELRAAM_COUNTER_START_YEAR, TELRAAM_COUNTER_START_MONTH, 1)
        from_date = datetime.strftime(from_date, TIME_FORMAT)

    end_date = datetime.now().strftime(TIME_FORMAT)
    logger.info(f"Fetching Telraam data from {from_date} to {end_date}")

    df_created = pd.DataFrame()
    reports = []
    min_delta_hours = 1_000_000
    cameras = get_telraam_cameras()
    for camera in cameras:
        report, delta_hours = get_hourly_data(
            from_date, end_date, camera["instance_id"]
        )
        if report:
            logger.info(
                f"Camera {camera['instance_id']} imported to {report[-1]['date']}"
            )
        else:
            f"Imported empty report for camera {camera['instance_id']}"

        # NOTE, reports length can vary as some have less data.
        if delta_hours <= min_delta_hours:
            min_delta_hours = delta_hours
        reports.append({"camera": camera, "report": report})

    columns = {}
    columns[INDEX_COLUMN_NAME] = []
    # NOTE, rows are only populated to that datetime where all cameras has data.
    delta_hours = min_delta_hours
    for i, report in enumerate(reports):
        for hour in range(delta_hours):
            if i == 0:
                columns[INDEX_COLUMN_NAME].append(reports[0]["report"][hour]["date"])
            mappings = get_mappings(report["camera"]["mac"])
            for mapping in mappings.items():
                # key is the name of the column, e.g., name_ak
                key = mapping[1]
                value_key = mapping[0]
                values_list = columns.get(key, [])
                if HEAVY in value_key:
                    # add heavy values to car column, as the mapping is same.
                    values_list[-1] += report["report"][hour][value_key]
                else:
                    values_list.append(report["report"][hour][value_key])
                columns[key] = values_list
    df_created = pd.DataFrame(data=columns, index=columns["startTime"])
    df_created = df_created.drop(columns=[INDEX_COLUMN_NAME], axis=1)
    if df.empty:
        df = df_created
    else:
        df = pd.concat([df, df_created], axis=0)
    df.index.rename(INDEX_COLUMN_NAME, inplace=True)
    df = df.fillna(0)
    df = df.astype(int)
    df.to_csv(csv_file)
    logger.info(
        f"Telraam data imported until {df.index[-1]} and DataFrame saved to {csv_file}"
    )


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Importing Telraam data...")
        save_dataframe()
