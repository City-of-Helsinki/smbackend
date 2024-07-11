"""
To run test:
pytest -m test_import_counter_data
Usage:
see README.md
"""

import gc
import logging
from datetime import datetime

import dateutil.parser
import pandas as pd
import pytz
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from eco_counter.constants import (
    COUNTER_CHOICES_STR,
    COUNTER_START_YEARS,
    COUNTERS,
    ECO_COUNTER,
    INDEX_COLUMN_NAME,
    LAM_COUNTER,
    TELRAAM_COUNTER,
    TELRAAM_COUNTER_START_MONTH,
    TRAFFIC_COUNTER,
    TRAFFIC_COUNTER_START_YEAR,
)
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

from .utils import (
    check_counters_argument,
    gen_eco_counter_test_csv,
    get_data_from_date,
    get_data_until_date,
    get_eco_counter_csv,
    get_is_active,
    get_lam_counter_csv,
    get_or_create_telraam_station,
    get_sensor_types,
    get_telraam_data_frames,
    get_test_dataframe,
    get_traffic_counter_csv,
    save_stations,
)

logger = logging.getLogger("eco_counter")
assert settings.ECO_COUNTER_STATIONS_URL, "Missing ECO_COUNTER_STATIONS_URL in env."
assert (
    settings.ECO_COUNTER_OBSERVATIONS_URL
), "Missing ECO_COUNTER_OBSERVATIONS_URL in env."
assert (
    settings.TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL
), "Missing TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL in env."
# Threshold for too big(errorneous?) values in source data.
# The value is calculated by estimating one car passing every second
# on a six lane road during the sample time (15min), 15min*60s*6lanes.
# If the value is greater than the threshold value the value is set to 0.
ERRORNEOUS_VALUE_THRESHOLD = 5400
TIMEZONE = pytz.timezone("Europe/Helsinki")
"""
Movement types:
(A)uto, car
(P)yörä, bicycle
(J)alankulkija, pedestrian
(B)ussi, bus
Direction types:
(K)eskustaan päin, towards the center
(P)poispäin keskustasta, away from the center
So for the example column with prefix "ap" contains data for cars moving away from the center.
The naming convention is derived from the eco-counter source data that was the
original data source.

"""
STATION_TYPES = [
    ("ak", "ap", "at"),
    ("pk", "pp", "pt"),
    ("jk", "jp", "jt"),
    ("bk", "bp", "bt"),
]

TYPE_DIRS = ["AK", "AP", "JK", "JP", "BK", "BP", "PK", "PP"]
ALL_TYPE_DIRS = TYPE_DIRS + ["AT", "JT", "BT", "PT"]


def delete_tables(
    csv_data_sources=[ECO_COUNTER, TRAFFIC_COUNTER, LAM_COUNTER, TELRAAM_COUNTER],
):
    for csv_data_source in csv_data_sources:
        for station in Station.objects.filter(csv_data_source=csv_data_source):
            Year.objects.filter(station=station).delete()
        ImportState.objects.filter(csv_data_source=csv_data_source).delete()


def save_hour_data_values(hour_data, values):
    for td in ALL_TYPE_DIRS:
        setattr(hour_data, f"values_{td.lower()}", values[td])
    hour_data.save()


def save_values(values, dst_obj):
    for station_types in STATION_TYPES:
        setattr(dst_obj, f"value_{station_types[0]}", values[station_types[0]])
        setattr(dst_obj, f"value_{station_types[1]}", values[station_types[1]])
        setattr(
            dst_obj,
            f"value_{station_types[2]}",
            values[station_types[0]] + values[station_types[1]],
        )
    dst_obj.save()


def add_values(values, dst_obj):
    """
    Populate values for all movement types and directions for a station.
    """
    for station_types in STATION_TYPES:
        key = f"value_{station_types[0]}"
        k_val = getattr(dst_obj, key, 0) + values[station_types[0]]
        setattr(dst_obj, key, k_val)
        key = f"value_{station_types[1]}"
        p_val = getattr(dst_obj, key, 0) + values[station_types[1]]
        setattr(dst_obj, key, p_val)
        key = f"value_{station_types[2]}"
        t_val = (
            getattr(dst_obj, key, 0)
            + values[station_types[0]]
            + values[station_types[1]]
        )
        setattr(dst_obj, key, t_val)
    dst_obj.save()


def get_values(sum_series, station_name):
    """
    Returns a dict containing the aggregated sum value for every movement type and direction.
    """
    values = {}
    for type_dir in TYPE_DIRS:
        key = f"{station_name} {type_dir}"
        values[type_dir.lower()] = sum_series.get(key, 0)
    return values


def save_years(df, stations):
    logger.info("Saving years...")
    years = df.groupby(df.index.year)
    for index, row in years:
        logger.info(f"Saving year {index}")
        sum_series = row.sum()
        for station in stations:
            year, _ = Year.objects.get_or_create(station=station, year_number=index)
            values = get_values(sum_series, station.name)
            year_data, _ = YearData.objects.get_or_create(year=year, station=station)
            save_values(values, year_data)


def save_months(df, stations):
    logger.info("Saving months...")
    months = df.groupby([df.index.year, df.index.month])
    for index, row in months:
        year_number, month_number = index
        logger.info(f"Saving month {month_number} of year {year_number}")
        sum_series = row.sum()
        for station in stations:
            year, _ = Year.objects.get_or_create(
                station=station, year_number=year_number
            )
            month, _ = Month.objects.get_or_create(
                station=station, year=year, month_number=month_number
            )
            values = get_values(sum_series, station.name)
            month_data, _ = MonthData.objects.get_or_create(
                year=year, month=month, station=station
            )
            save_values(values, month_data)


def save_current_year(stations, year_number, end_month_number):
    logger.info(f"Saving current year {year_number}")
    for station in stations:
        year, _ = Year.objects.get_or_create(station=station, year_number=year_number)
        year_data, _ = YearData.objects.get_or_create(station=station, year=year)
        for station_types in STATION_TYPES:
            setattr(year_data, f"value_{station_types[0]}", 0)
            setattr(year_data, f"value_{station_types[1]}", 0)
            setattr(year_data, f"value_{station_types[2]}", 0)
        for month_number in range(1, end_month_number + 1):
            month, _ = Month.objects.get_or_create(
                station=station, year=year, month_number=month_number
            )
            month_data, _ = MonthData.objects.get_or_create(
                station=station, month=month, year=year
            )
            for station_types in STATION_TYPES:
                for i in range(3):
                    key = f"value_{station_types[i]}"
                    m_val = getattr(month_data, key, 0)
                    y_val = getattr(year_data, key, 0)
                    setattr(year_data, key, m_val + y_val)
        year_data.save()


def save_weeks(df, stations):
    logger.info("Saving weeks...")
    weeks = df.groupby([df.index.year, df.index.isocalendar().week])
    for index, row in weeks:
        year_number, week_number = index
        logger.info(f"Saving week number {week_number} of year {year_number}")
        sum_series = row.sum()
        for station in stations:
            year = Year.objects.get(station=station, year_number=year_number)
            week, _ = Week.objects.get_or_create(
                station=station,
                week_number=week_number,
                years__year_number=year_number,
            )
            if week.years.count() == 0:
                week.years.add(year)

            values = get_values(sum_series, station.name)
            week_data, _ = WeekData.objects.get_or_create(station=station, week=week)
            save_values(values, week_data)


def save_days(df, stations):
    logger.info("Saving days...")
    days = df.groupby(
        [df.index.year, df.index.month, df.index.isocalendar().week, df.index.day]
    )
    prev_week_number = None
    for index, row in days:
        year_number, month_number, week_number, day_number = index

        date = datetime(year_number, month_number, day_number)
        sum_series = row.sum()
        for station in stations:
            year = Year.objects.get(station=station, year_number=year_number)
            month = Month.objects.get(
                station=station, year=year, month_number=month_number
            )
            week = Week.objects.get(
                station=station, years=year, week_number=week_number
            )
            day, _ = Day.objects.get_or_create(
                station=station,
                date=date,
                weekday_number=date.weekday(),
                year=year,
                month=month,
                week=week,
            )
            values = get_values(sum_series, station.name)
            day_data, _ = DayData.objects.get_or_create(station=station, day=day)
            save_values(values, day_data)
        if not prev_week_number or prev_week_number != week_number:
            prev_week_number = week_number
            logger.info(f"Saved days for week {week_number} of year {year_number}")


def save_hours(df, stations):
    logger.info("Saving hours...")
    hours = df.groupby([df.index.year, df.index.month, df.index.day, df.index.hour])
    for i_station, station in enumerate(stations):
        prev_day_number = None
        prev_month_number = None
        values = {k: [] for k in ALL_TYPE_DIRS}
        for index, row in hours:
            sum_series = row.sum()
            year_number, month_number, day_number, _ = index
            if not prev_day_number:
                prev_day_number = day_number
            if not prev_month_number:
                prev_month_number = month_number

            if day_number != prev_day_number or month_number != prev_month_number:
                """
                If day or month changed. Save the hours for the day and clear the values dict.
                """
                if month_number != prev_month_number:
                    prev_day_number = day_number
                day = Day.objects.get(
                    date=datetime(year_number, month_number, prev_day_number),
                    station=station,
                )
                hour_data, _ = HourData.objects.get_or_create(station=station, day=day)
                save_hour_data_values(hour_data, values)
                values = {k: [] for k in ALL_TYPE_DIRS}
                # output logger only when last station is saved
                if i_station == len(stations) - 1:
                    logger.info(
                        f"Saved hour data for day {prev_day_number}, month {prev_month_number} year {year_number}"
                    )
                prev_day_number = day_number
                prev_month_number = month_number
            # Add data to values dict for an hour
            for station_types in STATION_TYPES:
                for i in range(len(station_types)):
                    if i < 2:
                        dir_key = f"{station.name} {station_types[i].upper()}"
                        val = sum_series.get(dir_key, 0)
                    else:
                        k_key = f"{station.name} {station_types[0].upper()}"
                        p_key = f"{station.name} {station_types[1].upper()}"
                        val = sum_series.get(p_key, 0) + sum_series.get(k_key, 0)
                    values_key = station_types[i].upper()
                    values[values_key].append(val)

        # Save hour datas for the last day in data frame
        day, _ = Day.objects.get_or_create(
            date=datetime(year_number, month_number, day_number),
            station=station,
        )
        hour_data, _ = HourData.objects.get_or_create(station=station, day=day)
        save_hour_data_values(hour_data, values)


def save_observations(csv_data, start_time, csv_data_source=ECO_COUNTER, station=None):
    import_state = ImportState.objects.get(csv_data_source=csv_data_source)
    # Populate stations list, this is used to set/lookup station relations.
    if not station:
        stations = [
            station
            for station in Station.objects.filter(csv_data_source=csv_data_source)
        ]
    else:
        stations = [station]
    df = csv_data
    df["Date"] = pd.to_datetime(df["startTime"], format="%Y-%m-%dT%H:%M")
    df = df.drop("startTime", axis=1)
    df = df.set_index("Date")
    # Fill missing cells with the value 0
    df = df.fillna(0)
    # Set negative numbers to 0
    df = df.clip(lower=0)
    # Set values higher than ERRORNEOUS_VALUES_THRESHOLD to 0
    df[df > ERRORNEOUS_VALUE_THRESHOLD] = 0
    if not import_state.current_year_number:
        # In initial import populate all years.
        save_years(df, stations)
    save_months(df, stations)
    if import_state.current_year_number:
        end_month_number = df.index[-1].month
        save_current_year(stations, start_time.year, end_month_number)

    save_weeks(df, stations)
    save_days(df, stations)
    save_hours(df, stations)
    end_date = df.index[-1]
    import_state.current_year_number = end_date.year
    import_state.current_month_number = end_date.month
    import_state.current_day_number = end_date.day
    import_state.save()
    add_additional_data_to_stations(csv_data_source)
    logger.info(f"Imported observations until:{str(end_date)}")


def save_telraam_data(start_time):
    data_frames = get_telraam_data_frames(start_time.date())
    for item in data_frames.items():
        if len(item) == 0:
            logger.error("Found Telraam dataframe without data")
            break
        station = get_or_create_telraam_station(item[0])
        logger.info(f"Saving Telraam station {station.name}")
        # Save dataframes for the camera(station)
        for csv_data in item[1]:
            start_time = csv_data.iloc[0][0].to_pydatetime()
            save_observations(
                csv_data,
                start_time,
                csv_data_source=TELRAAM_COUNTER,
                station=station,
            )


def handle_initial_import(counter):
    logger.info(f"Deleting tables for: {counter}")
    delete_tables(csv_data_sources=[counter])
    ImportState.objects.filter(csv_data_source=counter).delete()
    import_state = ImportState.objects.create(csv_data_source=counter)
    logger.info(f"Retrieving stations for {counter}.")
    # As Telraam counters are dynamic, i.e., location can change,
    # create Stations while the CSV data is processed as location info
    # is bundled into the CSV files.
    if counter == TELRAAM_COUNTER:
        Station.objects.filter(csv_data_source=counter).delete()
    else:
        save_stations(counter)
    return import_state


def get_start_time(counter, import_state):
    if import_state.current_year_number and import_state.current_month_number:
        start_time = "{year}-{month}-1T00:00".format(
            year=import_state.current_year_number,
            month=import_state.current_month_number,
        )
    else:
        start_month = (
            TELRAAM_COUNTER_START_MONTH if counter == TELRAAM_COUNTER else "01"
        )
        start_time = f"{COUNTER_START_YEARS[counter]}-{start_month}-01"

    start_time = dateutil.parser.parse(start_time)
    start_time = TIMEZONE.localize(start_time)
    # The timeformat for the input data is : 2020-03-01T00:00
    # Convert starting time to input datas timeformat
    return start_time


def get_csv_data(counter, import_state, start_time, verbose=True):
    match counter:
        # case COUNTERS.TELRAAM_COUNTER:
        # Telraam counters are handled differently due to their dynamic nature
        case COUNTERS.LAM_COUNTER:
            csv_data = get_lam_counter_csv(start_time.date())
        case COUNTERS.ECO_COUNTER:
            csv_data = get_eco_counter_csv()
        case COUNTERS.TRAFFIC_COUNTER:
            if import_state.current_year_number:
                start_year = import_state.current_year_number
            else:
                start_year = TRAFFIC_COUNTER_START_YEAR
            csv_data = get_traffic_counter_csv(start_year=start_year)

    start_time_string = start_time.strftime("%Y-%m-%dT%H:%M")
    start_index = csv_data.index[
        csv_data[INDEX_COLUMN_NAME] == start_time_string
    ].values[0]
    if verbose:
        # As LAM data is fetched with a timespan, no index data is available, instead display start_time.
        if counter == LAM_COUNTER:
            logger.info(f"Starting saving observations at time:{start_time}")
        else:
            logger.info(f"Starting saving observations at index:{start_index}")

    csv_data = csv_data[start_index:]
    return csv_data


def import_data(counters, initial_import=False, force=False):
    for counter in counters:
        logger.info(f"Importing/counting data for {counter}...")
        import_state = ImportState.objects.filter(csv_data_source=counter).first()

        # Before deleting state and data, check that data is available.
        if not force and import_state and initial_import:
            start_time = get_start_time(counter, import_state)
            # Handle Telraam data differently in save_telraam_data method as the souurce data is static CSV files.
            if counter != TELRAAM_COUNTER:
                csv_data = get_csv_data(
                    counter, import_state, start_time, verbose=False
                )
                if len(csv_data) == 0:
                    logger.info(
                        "No data to retrieve, skipping initial import. Use --force to discard."
                    )
                    continue

        if initial_import:
            handle_initial_import(counter)
            import_state = ImportState.objects.filter(csv_data_source=counter).first()

        if not import_state:
            logger.error(
                "ImportState instance not found, try importing with the '--init' argument."
            )
            break

        start_time = get_start_time(counter, import_state)

        if counter == TELRAAM_COUNTER:
            save_telraam_data(start_time)
        else:
            csv_data = get_csv_data(counter, import_state, start_time)
            save_observations(
                csv_data,
                start_time,
                csv_data_source=counter,
            )
            # Try to free some memory
            del csv_data
            gc.collect()


def add_additional_data_to_stations(csv_data_source):
    logger.info(f"Updating {csv_data_source} stations informations...")
    for station in Station.objects.filter(csv_data_source=csv_data_source):
        station.data_from_date = get_data_from_date(station)
        station.data_until_date = get_data_until_date(station)
        station.sensor_types = get_sensor_types(station)
        station.is_active = get_is_active(station)
        station.save()


class Command(BaseCommand):
    help = "Imports traffic counter data in the Turku region."

    def add_arguments(self, parser):
        parser.add_argument(
            "--initial-import",
            type=str,
            nargs="+",
            default=False,
            help=f"For given counters in arguments deletes all tables before importing, imports stations and\
                 starts importing from row 0. The counter arguments are: {COUNTER_CHOICES_STR}",
        )
        parser.add_argument(
            "--test-counter",
            type=int,
            nargs="+",
            default=False,
            help="Test importing of data. Uses Generated pandas dataframe.",
        )
        parser.add_argument(
            "--counters",
            type=str,
            nargs="+",
            default=False,
            help=f"Import specific counter(s) data, choices are: {COUNTER_CHOICES_STR}.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force the initial import and discard data check",
        )

    def handle(self, *args, **options):
        initial_import_counters = None
        start_time = None
        initial_import = False
        force = options.get("force", False)
        if options["initial_import"]:
            if len(options["initial_import"]) == 0:
                raise CommandError(
                    f"Specify the counter(s), choices are: {COUNTER_CHOICES_STR}."
                )
            else:
                initial_import_counters = options["initial_import"]
                initial_import = True

        if options["test_counter"]:
            logger.info("Testing eco_counter importer.")
            counter = options["test_counter"][0]
            start_time = options["test_counter"][1]
            end_time = options["test_counter"][2]
            ImportState.objects.get_or_create(csv_data_source=counter)
            test_dataframe = get_test_dataframe(counter)
            csv_data = gen_eco_counter_test_csv(
                test_dataframe.keys(), start_time, end_time
            )
            save_observations(
                csv_data,
                start_time,
                csv_data_source=counter,
            )

        # Import if counters arg or initial import.
        if options["counters"] or initial_import_counters:
            if not initial_import_counters:
                # run with counters argument
                counters = options["counters"]
            else:
                counters = initial_import_counters
            check_counters_argument(counters)
            import_data(counters, initial_import, force)
