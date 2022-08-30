"""
Usage:
For initial import or changes in the stations:
python manage.py import-counter-data --initial-import
otherwise for incremental import:
python manage.py import-counter-data

Brief explanation of the import alogithm:
1. Import the stations.
2. Read the csv file as a pandas DataFrame.
3. Reads the year and month from the ImportState.
4. Set the import to start from that year and month, the import always begins
 from the first day and time 00:00:00 of the month in state, i.e. the longest
 timespan that is imported is one month and the shortest is 15min, depending
 on the import state.
5. Delete tables(HourData, Day, DayData and Week) that will be repopulated. *
6. Set the current state to state variables: current_years, currents_months,
 current_weeks, these dictionaries holds references to the model instances.
 Every station has its own state variables and the key is the name of the station.
7. Iterate through all the rows
    7.1 Read the time
    7.2 Read the current year, month, week and day number.
    7.3 If index % 4 == 0 save current hour to current_hours state, the input
     data has a sample rateof 15min, and the precision stored while importing
    is One hour.
    7.4 If day number has changed save hourly and day data.
    7.4.1 If Year, month or week number has changed. Save this data, create new tables
          and update references to state variables.
    7.4.2 Create new day tables using the current state variables(year, month week),
          update day state variable. Create HourData tables and update current_hours
          state variable. HourData tables are the only tables that contains data that are
          in the state, thus they are updated every fourth iteration. (15min samples to 1h)
    8.6 Iterate through all the columns, except the first that holds the time.
    8.6.1 Store the sampled data to current_hour state for every station,
           every mode of transportaion and direction.
9. Finally store all data in states that has not been saved.
10. Save import state.

* If executed with the --init-tables flag, the imports will start from the beginning
of the .csv file, 1.1.2020. for the eco counter and 1.1.2015 for the traffic counter.

"""

import logging
import math
import re
from datetime import datetime, timedelta

import dateutil.parser
import pytz
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from eco_counter.models import (
    Day,
    DayData,
    ECO_COUNTER,
    ECO_COUNTER_START_YEAR,
    HourData,
    ImportState,
    Month,
    MonthData,
    Station,
    TRAFFIC_COUNTER,
    TRAFFIC_COUNTER_START_YEAR,
    Week,
    WeekData,
    Year,
    YearData,
)

from .utils import (
    gen_eco_counter_test_csv,
    get_eco_counter_csv,
    get_traffic_counter_csv,
    save_eco_counter_stations,
    save_traffic_counter_stations,
)

logger = logging.getLogger("eco_counter")
assert settings.ECO_COUNTER_STATIONS_URL, "Missing ECO_COUNTER_STATIONS_URL in env."
assert (
    settings.ECO_COUNTER_OBSERVATIONS_URL
), "Missing ECO_COUNTER_OBSERVATIONS_URL in env."
assert (
    settings.TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL
), "Missing TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL in env."


class Command(BaseCommand):
    help = "Imports Turku Traffic Volumes"

    TIMESTAMP_COL_NAME = "startTime"
    TIMEZONE = pytz.timezone("Europe/Helsinki")
    STATION_TYPES = [
        ("ak", "ap", "at"),
        ("pk", "pp", "pt"),
        ("jk", "jp", "jt"),
        ("bk", "bp", "bt"),
    ]

    def delete_tables(self):
        HourData.objects.all().delete()
        DayData.objects.all().delete()
        Day.objects.all().delete()
        WeekData.objects.all().delete()
        Week.objects.all().delete()
        Month.objects.all().delete()
        MonthData.objects.all().delete()
        Year.objects.all().delete()
        YearData.objects.all().delete()
        Station.objects.all().delete()
        ImportState.objects.all().delete()

    def calc_and_save_cumulative_data(self, src_obj, dst_obj):

        for station_types in self.STATION_TYPES:
            setattr(dst_obj, f"value_{station_types[0]}", 0)
            setattr(dst_obj, f"value_{station_types[1]}", 0)
            setattr(dst_obj, f"value_{station_types[2]}", 0)

        for src in src_obj:
            for station_types in self.STATION_TYPES:
                setattr(
                    dst_obj,
                    f"value_{station_types[0]}",
                    getattr(dst_obj, f"value_{station_types[0]}")
                    + getattr(src, f"value_{station_types[0]}"),
                )
                setattr(
                    dst_obj,
                    f"value_{station_types[1]}",
                    getattr(dst_obj, f"value_{station_types[1]}")
                    + getattr(src, f"value_{station_types[1]}"),
                )
                setattr(
                    dst_obj,
                    f"value_{station_types[2]}",
                    getattr(dst_obj, f"value_{station_types[2]}")
                    + getattr(src, f"value_{station_types[2]}"),
                )
        dst_obj.save()

    def create_and_save_year_data(self, stations, current_years):
        for station in stations:
            year = current_years[station]
            year_data = YearData.objects.update_or_create(
                year=year, station=stations[station]
            )[0]
            self.calc_and_save_cumulative_data(year.month_data.all(), year_data)

    def create_and_save_month_data(self, stations, current_months, current_years):
        for station in stations:
            month = current_months[station]
            month_data = MonthData.objects.update_or_create(
                month=month, station=stations[station], year=current_years[station]
            )[0]
            day_data = DayData.objects.filter(day__month=month)
            self.calc_and_save_cumulative_data(day_data, month_data)

    def create_and_save_week_data(self, stations, current_weeks):
        for station in stations:
            week = current_weeks[station]
            week_data = WeekData.objects.update_or_create(
                week=week, station=stations[station]
            )[0]
            day_data = DayData.objects.filter(day__week=week)
            self.calc_and_save_cumulative_data(day_data, week_data)

    def create_and_save_day_data(self, stations, current_hours, current_days):
        for station in stations:
            day_data = DayData.objects.create(
                station=stations[station], day=current_days[station]
            )
            current_hour = current_hours[station]
            for station_types in self.STATION_TYPES:
                setattr(
                    day_data,
                    f"value_{station_types[0]}",
                    sum(getattr(current_hour, f"values_{station_types[0]}")),
                )
                setattr(
                    day_data,
                    f"value_{station_types[1]}",
                    sum(getattr(current_hour, f"values_{station_types[1]}")),
                )
                setattr(
                    day_data,
                    f"value_{station_types[2]}",
                    sum(getattr(current_hour, f"values_{station_types[2]}")),
                )
            day_data.save()

    def save_hour_data(self, current_hour, current_hours):
        for station in current_hour:
            hour_data = current_hours[station]

            for station_type in self.STATION_TYPES:
                # keskustaan päin
                k_field = station_type[0]
                k_value = 0
                # poispäin keskustastat
                p_field = station_type[1]
                p_value = 0
                total_field = station_type[2]
                if k_field.upper() in current_hour[station]:
                    k_value = current_hour[station][k_field.upper()]
                    getattr(hour_data, f"values_{k_field}").append(k_value)

                if p_field.upper() in current_hour[station]:
                    p_value = current_hour[station][p_field.upper()]
                    getattr(hour_data, f"values_{p_field}").append(p_value)
                getattr(hour_data, f"values_{total_field}").append(k_value + p_value)
            hour_data.save()

    def get_station_name_and_type(self, column):
        # Station type is always: A|P|J|B + K|P
        station_type = re.findall("[APJB][PK]", column)[0]
        station_name = column.replace(station_type, "").strip()
        return station_name, station_type

    def save_observations(
        self, csv_data, start_time, column_names, csv_data_source=ECO_COUNTER
    ):
        stations = {}
        # Populate stations dict, used to lookup station relations
        for station in Station.objects.filter(csv_data_source=csv_data_source):
            stations[station.name] = station
        # state variable for the current hour that is calucalted for every iteration(15min)
        current_hour = {}
        current_hours = {}
        current_days = {}
        current_weeks = {}
        current_months = {}
        current_years = {}
        import_state = ImportState.objects.get(csv_data_source=csv_data_source)
        rows_imported = import_state.rows_imported
        current_year_number = import_state.current_year_number
        current_month_number = import_state.current_month_number
        current_weekday_number = None

        current_week_number = int(start_time.strftime("%-V"))
        prev_weekday_number = start_time.weekday()
        prev_year_number = current_year_number
        prev_month_number = current_month_number
        prev_week_number = current_week_number
        current_time = None
        prev_time = None
        # All Hourly, daily and weekly data that are past the current_week_number
        # are delete thus they are repopulated.  HourData and DayData are deleted
        # thus their on_delete is set to models.CASCADE.
        Day.objects.filter(
            month__month_number=current_month_number,
            month__year__year_number=current_year_number,
        ).delete()
        for week_number in range(current_week_number + 1, current_week_number + 5):
            Week.objects.filter(
                week_number=week_number, years__year_number=current_year_number
            ).delete()

        # Set the references to the current state.
        for station in stations:
            current_years[station] = Year.objects.get_or_create(
                station=stations[station], year_number=current_year_number
            )[0]
            current_months[station] = Month.objects.get_or_create(
                station=stations[station],
                year=current_years[station],
                month_number=current_month_number,
            )[0]
            current_weeks[station] = Week.objects.get_or_create(
                station=stations[station],
                week_number=current_week_number,
                years__year_number=current_year_number,
            )[0]
            current_weeks[station].years.add(current_years[station])

        for index, row in csv_data.iterrows():
            try:
                timestamp = row.get(self.TIMESTAMP_COL_NAME, None)
                if type(timestamp) == str:
                    current_time = dateutil.parser.parse(timestamp)
                # When the time is changed due to daylight savings
                # Input data does not contain any timestamp for that hour, only data
                # so the current_time is calculated
                else:
                    current_time = prev_time + timedelta(minutes=15)
            except dateutil.parser._parser.ParserError:
                # If malformed time calcultate new current_time.
                current_time = prev_time + timedelta(minutes=15)

            current_time = self.TIMEZONE.localize(current_time)
            if prev_time:
                # Compare the utcoffset, if not equal the daylight saving has changed.
                if current_time.tzinfo.utcoffset(
                    current_time
                ) != prev_time.tzinfo.utcoffset(prev_time):
                    # Take the daylight saving time (dst) hour from the utcoffset
                    current_time_dst_hour = dateutil.parser.parse(
                        str(current_time.tzinfo.utcoffset(current_time))
                    )
                    prev_time_dst_hour = dateutil.parser.parse(
                        str(prev_time.tzinfo.utcoffset(prev_time))
                    )
                    # If the prev_time_dst_hour is less than current_time_dst_hour,
                    # then this is the hour clocks are changed backwards, i.e. wintertime
                    if prev_time_dst_hour < current_time_dst_hour:
                        # Add an hour where the values are 0, for the nonexistent hour 3:00-4:00
                        # To keep the hour data consistent with 24 hours.
                        logger.info(
                            "Detected daylight savings time change to summer. DateTime: {}".format(
                                current_time
                            )
                        )
                        temp_hour = {}
                        for station in stations:
                            temp_hour[station] = {}
                        for column in column_names[1:]:
                            station_name, station_type = self.get_station_name_and_type(
                                column
                            )
                            temp_hour[station_name][station_type] = 0
                        self.save_hour_data(temp_hour, current_hours)
            # print(f"Current_time: {current_time} Year: {current_time.year}, I {index}")
            current_year_number = current_time.year
            current_week_number = int(current_time.strftime("%-V"))
            current_weekday_number = current_time.weekday()
            current_month_number = datetime.date(current_time).month

            # Adds data for an hour every fourth iteration, sample rate is 15min.
            if index % 4 == 0:
                self.save_hour_data(current_hour, current_hours)
                # Clear current_hour after storage, to get data for every hour.
                current_hour = {}

            if prev_weekday_number != current_weekday_number or not current_hours:
                # Store hour data if data exists.
                if current_hours:
                    self.create_and_save_day_data(stations, current_hours, current_days)
                current_hours = {}

                # Year, month, week tables are created before the day tables
                # to ensure correct relations.
                if prev_year_number != current_year_number or not current_years:
                    # if we have a prev_year_number and it is not the current_year_number store yearly data.
                    if prev_year_number:
                        self.create_and_save_year_data(stations, current_years)
                    for station in stations:
                        year = Year.objects.create(
                            year_number=current_year_number, station=stations[station]
                        )
                        current_years[station] = year
                        current_weeks[station].years.add(year)
                    prev_year_number = current_year_number

                if prev_month_number != current_month_number or not current_months:
                    if prev_month_number:
                        self.create_and_save_month_data(
                            stations, current_months, current_years
                        )
                    for station in stations:
                        month = Month.objects.create(
                            station=stations[station],
                            year=current_years[station],
                            month_number=current_month_number,
                        )
                        current_months[station] = month
                    prev_month_number = current_month_number

                if prev_week_number != current_week_number or not current_weeks:
                    if prev_week_number:
                        self.create_and_save_week_data(stations, current_weeks)
                    for station in stations:
                        week = Week.objects.create(
                            station=stations[station], week_number=current_week_number
                        )
                        week.years.add(current_years[station])
                        current_weeks[station] = week
                    prev_week_number = current_week_number

                for station in stations:
                    day = Day.objects.create(
                        station=stations[station],
                        date=current_time,
                        weekday_number=current_weekday_number,
                        week=current_weeks[station],
                        month=current_months[station],
                        year=current_years[station],
                    )
                    current_days[station] = day
                    hour_data = HourData.objects.create(
                        station=stations[station], day=current_days[station]
                    )
                    current_hours[station] = hour_data
                prev_weekday_number = current_weekday_number

            """
            Build the current_hour dict by iterating all cols in row.
            current_hour dict store the rows in a structured form.
            current_hour keys are the station names and every value contains a dict with the type as its key
            The type is: A|P|J|B (Auto, Pyöräilijä, Jalankulkija, Bussi) + direction P|K , e.g. "JK"
            current_hour[station][station_type] = value, e.g. current_hour["TeatteriSilta"]["PK"] = 6
            Note the first col is the self.TIMESTAMP_COL_NAME and is discarded, the rest are observations
            for every station.
            """
            for column in column_names[1:]:
                station_name, station_type = self.get_station_name_and_type(column)
                value = row[column]
                if math.isnan(value):
                    value = int(0)
                else:
                    value = int(row[column])
                # TODO threshold for too big(errorneous) values in source data
                # 15*60 seconds in 15min *4 lanes
                if value > 3600:
                    value = 0
                if station_name not in current_hour:
                    current_hour[station_name] = {}
                # if type exist in current_hour, we add the new value to get the hourly sample
                if station_type in current_hour[station_name]:
                    current_hour[station_name][station_type] = (
                        int(current_hour[station_name][station_type]) + value
                    )
                else:
                    current_hour[station_name][station_type] = value
            prev_time = current_time
        # Finally save hours, days, months etc. that are not fully populated.
        self.save_hour_data(current_hour, current_hours)
        self.create_and_save_day_data(stations, current_hours, current_days)
        self.create_and_save_week_data(stations, current_weeks)
        self.create_and_save_month_data(stations, current_months, current_years)
        self.create_and_save_year_data(stations, current_years)

        import_state.current_year_number = current_year_number
        import_state.current_month_number = current_month_number
        import_state.rows_imported = rows_imported + len(csv_data)
        import_state.save()
        logger.info("Imported observations until: " + str(current_time))

    def add_arguments(self, parser):
        parser.add_argument(
            "--initial-import",
            action="store_true",
            default=False,
            help="Deletes all tables before importing. Imports stations and\
                 starts importing from row 0.",
        )
        parser.add_argument(
            "--test-counter",
            type=int,
            nargs="+",
            default=False,
            help="Test importing of  data. Uses Generated pandas dataframe.",
        )
        parser.add_argument(
            "--counter",
            type=str,
            nargs="+",
            default=False,
            help=f"Import specific counter data, choices are: {ECO_COUNTER} and {TRAFFIC_COUNTER}.",
        )

    def handle(self, *args, **options):
        if options["initial_import"]:
            logger.info("Deleting tables")
            self.delete_tables()
            logger.info("Retrieving stations...")
            save_eco_counter_stations()
            save_traffic_counter_stations()

        logger.info("Retrieving observations...")

        start_time = None

        if options["test_counter"]:
            logger.info("Testing eco_counter importer.")
            counter = options["test_counter"][0]
            start_time = options["test_counter"][1]
            end_time = options["test_counter"][2]

            ImportState.objects.get_or_create(csv_data_source=counter)
            if counter == ECO_COUNTER:
                save_eco_counter_stations()
                eco_counter_csv = get_eco_counter_csv()
                csv_data = gen_eco_counter_test_csv(
                    eco_counter_csv.keys(), start_time, end_time
                )
                column_names = eco_counter_csv.keys()
            elif counter == TRAFFIC_COUNTER:
                save_traffic_counter_stations()
                # Building the complete CSV takes time, optimize by only using the
                # rows from year 2020 and onwards.
                traffic_counter_csv = get_traffic_counter_csv(start_year=2020)
                csv_data = gen_eco_counter_test_csv(
                    traffic_counter_csv.keys(), start_time, end_time
                )
                column_names = traffic_counter_csv.keys()
            else:
                raise CommandError("No valid counter argument given.")
            self.save_observations(
                csv_data, start_time, column_names, csv_data_source=counter
            )
        else:
            if options["counter"]:
                counters = options["counter"][0]
                if ECO_COUNTER != counters and TRAFFIC_COUNTER != counters:
                    raise CommandError(
                        f"Invalid counter type, valid types are {ECO_COUNTER} or {TRAFFIC_COUNTER}."
                    )
                counters = [counters]
            else:
                counters = [ECO_COUNTER, TRAFFIC_COUNTER]

            counter_data = {}
            if ECO_COUNTER in counters:
                eco_counter_csv = get_eco_counter_csv()
                counter_data[ECO_COUNTER] = {
                    "csv_data": eco_counter_csv,
                    "column_names": eco_counter_csv.keys(),
                    "start_year": ECO_COUNTER_START_YEAR,
                }
            if TRAFFIC_COUNTER in counters:
                traffic_counter_csv = get_traffic_counter_csv()
                counter_data[TRAFFIC_COUNTER] = {
                    "csv_data": traffic_counter_csv,
                    "column_names": traffic_counter_csv.keys(),
                    "start_year": TRAFFIC_COUNTER_START_YEAR,
                }
            for counter in counters:
                logger.info(f"Importing/counting data for {counter}...")
                if ImportState.objects.filter(csv_data_source=counter).exists():
                    import_state = ImportState.objects.filter(
                        csv_data_source=counter
                    ).first()
                else:
                    import_state = ImportState.objects.create(
                        csv_data_source=counter,
                        current_year_number=counter_data[counter]["start_year"],
                    )

                start_time = "{year}-{month}-1T00:00".format(
                    year=import_state.current_year_number,
                    month=import_state.current_month_number,
                )
                start_time = dateutil.parser.parse(start_time)
                start_time = self.TIMEZONE.localize(start_time)
                csv_data = counter_data[counter]["csv_data"]
                # The timeformat for the input data is : 2020-03-01T00:00
                # Convert starting time to input datas timeformat
                start_time_string = start_time.strftime("%Y-%m-%dT%H:%M")
                start_index = csv_data.index[
                    csv_data[self.TIMESTAMP_COL_NAME] == start_time_string
                ].values[0]
                logger.info("Starting import at index: {}".format(start_index))

                csv_data = csv_data[start_index:]
                self.save_observations(
                    csv_data,
                    start_time,
                    counter_data[counter]["column_names"],
                    csv_data_source=counter,
                )
