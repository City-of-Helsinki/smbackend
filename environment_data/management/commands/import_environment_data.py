import logging
from datetime import datetime
from functools import lru_cache

from django.core.management import BaseCommand, CommandError
from django.db import connection, reset_queries

import environment_data.management.commands.air_quality_constants as aq_constants
import environment_data.management.commands.air_quality_utils as am_utils
import environment_data.management.commands.weather_observation_constants as wo_constants
import environment_data.management.commands.weather_observation_utils as wo_utils
from environment_data.constants import (
    AIR_QUALITY,
    DATA_TYPE_CHOICES,
    DATA_TYPES,
    DATA_TYPES_FULL_NAME,
    WEATHER_OBSERVATION,
)
from environment_data.models import (
    Day,
    DayData,
    Hour,
    HourData,
    ImportState,
    Measurement,
    Month,
    MonthData,
    Parameter,
    Station,
    Week,
    WeekData,
    Year,
    YearData,
)

from .utils import (
    create_row,
    get_day_cached,
    get_month_cached,
    get_month_data_cached,
    get_or_create_day_row_cached,
    get_or_create_hour_row_cached,
    get_or_create_row,
    get_or_create_row_cached,
    get_row_cached,
    get_stations,
    get_week_cached,
    get_year_cached,
    get_year_data_cached,
)

logger = logging.getLogger(__name__)
VALID_DATA_TYPE_CHOICES = ", ".join(
    [item[0] + f" ({item[1]})" for item in DATA_TYPES_FULL_NAME.items()]
)
OBSERVABLE_PARAMETERS = (
    aq_constants.OBSERVABLE_PARAMETERS + wo_constants.OBSERVABLE_PARAMETERS
)


def get_measurements(mean_series, station_name):
    values = {}
    for parameter in OBSERVABLE_PARAMETERS:
        key = f"{station_name} {parameter}"
        value = mean_series.get(key, False)
        if value:
            values[parameter] = value
    return values


@lru_cache(maxsize=16)
def get_parameter(name):
    try:
        return Parameter.objects.get(name=name)
    except Parameter.DoesNotExist:
        return None


def get_measurement_objects(measurements):
    measurement_rows = []
    for item in measurements.items():
        parameter = get_parameter(item[0])
        measurement = Measurement(value=item[1], parameter=parameter)
        measurement_rows.append(measurement)
    return measurement_rows


def bulk_create_rows(data_model, model_objs, measurements, datas):
    logger.info(f"Bulk creating {len(model_objs)} {data_model.__name__} rows")
    data_model.objects.bulk_create(model_objs)
    logger.info(f"Bulk creating {len(measurements)} Measurement rows")
    Measurement.objects.bulk_create(measurements)
    for key in datas:
        data = datas[key]
        [data["data"].measurements.add(m) for m in data["measurements"]]


def save_years(df, stations):
    logger.info("Saving years...")
    years = df.groupby(df.index.year)
    for station in stations:
        measurements = []
        year_datas = {}
        year_data_objs = []
        for index, row in years:
            mean_series = row.mean().dropna()
            year, _ = get_or_create_row_cached(Year, (("year_number", index),))
            values = get_measurements(mean_series, station.name)
            year_data = YearData(station=station, year=year)
            year_data_objs.append(year_data)
            ret_mes = get_measurement_objects(values)
            measurements += ret_mes
            year_datas[index] = {"data": year_data, "measurements": ret_mes}
        bulk_create_rows(YearData, year_data_objs, measurements, year_datas)


def save_months(df, stations):
    logger.info("Saving months...")
    months = df.groupby([df.index.year, df.index.month])
    for station in stations:
        measurements = []
        month_datas = {}
        month_data_objs = []
        for index, row in months:
            year_number, month_number = index
            mean_series = row.mean().dropna()
            year = get_year_cached(year_number)
            month, _ = get_or_create_row_cached(
                Month,
                (("year", year), ("month_number", month_number)),
            )
            values = get_measurements(mean_series, station.name)
            month_data = MonthData(station=station, year=year, month=month)
            month_data_objs.append(month_data)
            ret_mes = get_measurement_objects(values)
            measurements += ret_mes
            month_datas[index] = {"data": month_data, "measurements": ret_mes}
        bulk_create_rows(MonthData, month_data_objs, measurements, month_datas)


def save_weeks(df, stations):
    """
    Note, weeks are stored in a different way, as a week can not be assigned
    distinctly to a year or month. So when importing incrementally the week
    or weeks in the dataframe can not be deleted before populating, thus the
    use of get_or_create.
    """
    logger.info("Saving weeks...")
    weeks = df.groupby([df.index.year, df.index.isocalendar().week])
    for i, station in enumerate(stations):
        for index, row in weeks:
            year_number, week_number = index
            if i == 0:
                logger.info(
                    f"Processing week number {week_number} of year {year_number}"
                )
            mean_series = row.mean().dropna()
            year = get_year_cached(year_number)
            week, _ = Week.objects.get_or_create(
                week_number=week_number,
                years__year_number=year_number,
            )
            if week.years.count() == 0:
                week.years.add(year)
            values = get_measurements(mean_series, station.name)
            week_data, _ = WeekData.objects.get_or_create(station=station, week=week)
            for item in values.items():
                parameter = get_parameter(item[0])
                if not week_data.measurements.filter(
                    value=item[1], parameter=parameter
                ):
                    measurement = Measurement.objects.create(
                        value=item[1], parameter=parameter
                    )
                    week_data.measurements.add(measurement)


def save_days(df, stations):
    logger.info("Processing days...")
    days = df.groupby(
        [df.index.year, df.index.month, df.index.isocalendar().week, df.index.day]
    )
    for station in stations:
        measurements = []
        day_datas = {}
        day_data_objs = []
        for index, row in days:
            year_number, month_number, week_number, day_number = index
            date = datetime(year_number, month_number, day_number)
            mean_series = row.mean().dropna()
            year = get_year_cached(year_number)
            month = get_month_cached(year, month_number)
            week = get_week_cached(year, week_number)
            day, _ = get_or_create_day_row_cached(date, year, month, week)
            values = get_measurements(mean_series, station.name)
            day_data = DayData(station=station, day=day)
            day_data_objs.append(day_data)
            ret_mes = get_measurement_objects(values)
            measurements += ret_mes
            day_datas[index] = {"data": day_data, "measurements": ret_mes}
        bulk_create_rows(DayData, day_data_objs, measurements, day_datas)


def save_hours(df, stations):
    logger.info("Processing hours... ")
    hours = df.groupby([df.index.year, df.index.month, df.index.day, df.index.hour])
    for station in stations:
        measurements = []
        hour_datas = {}
        hour_data_objs = []
        for index, row in hours:
            year_number, month_number, day_number, hour_number = index
            mean_series = row.mean().dropna()
            date = datetime(year_number, month_number, day_number)
            day = get_day_cached(date)
            hour, _ = get_or_create_hour_row_cached(day, hour_number)
            values = get_measurements(mean_series, station.name)
            hour_data = HourData(station=station, hour=hour)
            hour_data_objs.append(hour_data)
            ret_mes = get_measurement_objects(values)
            measurements += ret_mes
            hour_datas[index] = {"data": hour_data, "measurements": ret_mes}
        bulk_create_rows(HourData, hour_data_objs, measurements, hour_datas)


def save_current_year(stations, year_number, end_month_number):
    logger.info(f"Saving current year {year_number}")
    year = get_year_cached(year_number)
    for station in stations:
        measurements = {}
        num_months = 0
        for month_number in range(1, end_month_number + 1):
            month = get_month_cached(year, month_number)
            month_data = get_month_data_cached(station, month)
            if not month_data:
                logger.debug(f"Month number {month_number} not found")
                continue
            else:
                num_months += 1
            for measurement in month_data.measurements.all():
                key = measurement.parameter
                measurements[key] = measurements.get(key, 0) + measurement.value
        # get_or_create, if year changed the year needs to be created
        year_data, _ = get_or_create_row_cached(
            YearData,
            (
                ("station", station),
                ("year", year),
            ),
        )
        year_data.measurements.all().delete()
        for parameter in station.parameters.all():
            try:
                value = round(measurements[parameter] / num_months, 2)
            except KeyError:
                continue
            measurement = Measurement.objects.create(value=value, parameter=parameter)
            year_data.measurements.add(measurement)


def clear_cache():
    get_or_create_row_cached.cache_clear()
    get_or_create_hour_row_cached.cache_clear()
    get_or_create_day_row_cached.cache_clear()
    get_row_cached.cache_clear()
    get_year_cached.cache_clear()
    get_year_data_cached.cache_clear()
    get_month_cached.cache_clear()
    get_month_data_cached.cache_clear()
    get_week_cached.cache_clear()
    get_day_cached.cache_clear()
    get_parameter.cache_clear()


def delete_months(months_qs):
    month_datas_qs = MonthData.objects.filter(month__in=months_qs)
    [m.measurements.all().delete() for m in month_datas_qs]
    days_qs = Day.objects.filter(month__in=months_qs)
    day_datas_qs = DayData.objects.filter(day__in=days_qs)
    [m.measurements.all().delete() for m in day_datas_qs]
    hours_qs = Hour.objects.filter(day__in=days_qs)
    hour_datas_qs = HourData.objects.filter(hour__in=hours_qs)
    [m.measurements.all().delete() for m in hour_datas_qs]
    months_qs.delete()
    days_qs.delete()
    hours_qs.delete()


def save_measurements(df, data_type, initial_import=False):
    def delete_if_no_relations(items):
        for item in items:
            model = item[0]
            related_name = item[1]
            for row in model.objects.all():
                if not getattr(row, related_name).exists():
                    row.delete()

    stations = [station for station in Station.objects.filter(data_type=data_type)]
    end_date = df.index[-1]
    start_date = df.index[0]
    if initial_import:
        items = [
            (Year, "year_datas"),
            (Month, "month_datas"),
            (Week, "week_datas"),
            (Day, "day_datas"),
            (Hour, "hour_datas"),
        ]
        delete_if_no_relations(items)
        save_years(df, stations)
        save_months(df, stations)
    else:
        create_row(Year, {"year_number": start_date.year})
        year = get_year_cached(year_number=start_date.year)
        # Handle year change in dataframe
        if df.index[-1].year > df.index[0].year:
            months_qs = Month.objects.filter(
                year=year, month_number__gte=start_date.month, month_number__lte=12
            )
            delete_months(months_qs)
            create_row(Year, {"year_number": end_date.year})
            year = get_year_cached(year_number=end_date.year)
            Month.objects.filter(
                year=year, month_number__gte=1, month_number__lte=end_date.month
            )
            save_months(df, stations)
            save_current_year(stations, start_date.year, 12)
            save_current_year(stations, end_date.year, end_date.month)
        else:
            months_qs = Month.objects.filter(
                year=year,
                month_number__gte=start_date.month,
                month_number__lte=end_date.month,
            )
            delete_months(months_qs)
            save_months(df, stations)
            save_current_year(stations, start_date.year, end_date.month)

    save_weeks(df, stations)
    save_days(df, stations)
    save_hours(df, stations)
    import_state = ImportState.objects.get(data_type=data_type)
    import_state.year_number = end_date.year
    import_state.month_number = end_date.month
    import_state.save()
    if logger.level <= logging.DEBUG:
        queries_time = sum([float(s["time"]) for s in connection.queries])
        logger.debug(
            f"queries total execution time: {queries_time} Num queries: {len(connection.queries)}"
        )
        reset_queries()
        logger.debug(
            f"get_or_create_row_cached {get_or_create_row_cached.cache_info()}"
        )
        logger.debug(
            f"get_or_create_hour_row_cached {get_or_create_hour_row_cached.cache_info()}"
        )
        logger.debug(
            f"get_or_create_day_row_cached {get_or_create_day_row_cached.cache_info()}"
        )
        logger.debug(f"get_row_cached  {get_row_cached.cache_info()}")
        logger.debug(f"get_year_cached {get_year_cached.cache_info()}")
        logger.debug(f"get_year_cached {get_year_data_cached.cache_info()}")
        logger.debug(f"get_month_cached {get_month_cached.cache_info()}")
        logger.debug(f"get_month_cached {get_month_data_cached.cache_info()}")
        logger.debug(f"get_week_cached {get_week_cached.cache_info()}")
        logger.debug(f"get_day_cached {get_day_cached.cache_info()}")
        logger.debug(f"get_parameter {get_parameter.cache_info()}")


def save_parameter_types(df, data_type, initial_import=False):
    if initial_import:
        Parameter.objects.filter(data_type=data_type).delete()
    for station in Station.objects.filter(data_type=data_type):
        for parameter_name in OBSERVABLE_PARAMETERS:
            key = f"{station.name} {parameter_name}"
            if key in df.columns:
                parameter, _ = get_or_create_row(Parameter, {"name": parameter_name})
                station.parameters.add(parameter)


def save_stations(stations, data_type, initial_import_stations=False):
    num_created = 0
    if initial_import_stations:
        Station.objects.filter(data_type=data_type).delete()
    object_ids = list(Station.objects.all().values_list("id", flat=True))
    for station in stations:
        obj, created = get_or_create_row(
            Station,
            {
                "name": station["name"],
                "location": station["location"],
                "geo_id": station["geoId"],
                "data_type": data_type,
            },
        )
        if obj.id in object_ids:
            object_ids.remove(obj.id)
        if created:
            num_created += 1
    Station.objects.filter(id__in=object_ids).delete()
    logger.info(f"Deleted {len(object_ids)} obsolete environment data stations")
    num_stations = Station.objects.all().count()
    logger.info(
        f"Created {num_created} environment data stations of total {num_stations}."
    )


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--initial-import",
            type=str,
            nargs="+",
            default=False,
            help="Delete all data and reset import state befor importing",
        )
        parser.add_argument(
            "--initial-import-with-stations",
            type=str,
            nargs="+",
            default=False,
            help="Delete all data, all stations and reset import state befor importing",
        )
        parser.add_argument(
            "--data-types",
            type=str,
            nargs="+",
            default=False,
            help=f"Import environment data, choices are: {DATA_TYPE_CHOICES}.",
        )

    def check_data_types_argument(self, data_types):
        for data_type in data_types:
            if data_type not in [AIR_QUALITY, WEATHER_OBSERVATION]:
                raise CommandError(
                    f"Invalid data type, valid types are: {VALID_DATA_TYPE_CHOICES}."
                )

    def handle(self, *args, **options):
        start_time = datetime.now()
        initial_import = options.get("initial_import", False)
        initial_import_stations = options.get("initial_import_with_stations", False)

        if initial_import_stations:
            data_types = initial_import_stations
        elif initial_import:
            data_types = initial_import
        else:
            data_types = options.get("data_types", False)
        if not data_types:
            logger.info(
                f"No data type provided, choices are: {VALID_DATA_TYPE_CHOICES}"
            )
            return
        self.check_data_types_argument(data_types)

        initial_import = bool(initial_import or initial_import_stations)
        for data_type in data_types:
            if initial_import:
                ImportState.objects.filter(data_type=data_type).delete()
                start_year = None
                match data_type:
                    case DATA_TYPES.AIR_QUALITY:
                        start_year = aq_constants.START_YEAR
                    case DATA_TYPES.WEATHER_OBSERVATION:
                        start_year = wo_constants.START_YEAR
                    case _:
                        start_year = 2010

                import_state = ImportState.objects.create(
                    data_type=data_type,
                    year_number=start_year,
                    month_number=1,
                )
            else:
                import_state = ImportState.objects.get(data_type=data_type)

            match data_type:
                case DATA_TYPES.AIR_QUALITY:
                    stations = get_stations(aq_constants.STATION_MATCH_STRINGS)
                    df = am_utils.get_dataframe(
                        stations,
                        import_state.year_number,
                        import_state.month_number,
                        initial_import,
                    )
                case DATA_TYPES.WEATHER_OBSERVATION:
                    stations = get_stations(wo_constants.STATION_MATCH_STRINGS)
                    df = wo_utils.get_dataframe(
                        stations,
                        import_state.year_number,
                        import_state.month_number,
                        initial_import,
                    )
            save_stations(
                stations, data_type, initial_import_stations=initial_import_stations
            )
            save_parameter_types(df, data_type, initial_import)
            save_measurements(df, data_type, initial_import)
            logger.info(
                f"Imported {DATA_TYPES_FULL_NAME[data_type]} observations until:{str(df.index[-1])}"
            )

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Imported environment data in: {duration}")
