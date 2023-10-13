from datetime import datetime

from rest_framework.exceptions import ParseError

from .constants import DATA_TYPES, DATETIME_FORMATS, DAY, HOUR, MONTH, WEEK, YEAR


def validate_timestamp(timestamp_str, data_type):
    time_format = DATETIME_FORMATS[data_type]
    try:
        datetime.strptime(timestamp_str, time_format)
    except ValueError:
        raise ValueError(
            f"{timestamp_str} invalid format date format, valid format for type {data_type} is {time_format}"
        )


def get_start_and_end_and_year(filters, data_type):
    start = filters.get("start", None)
    end = filters.get("end", None)
    year = filters.get("year", None)

    if not start or not end:
        raise ParseError("Supply both 'start' and 'end' parameters")

    if YEAR not in data_type and not year:
        raise ParseError("Supply 'year' parameter")

    match data_type:
        case DATA_TYPES.DAY:
            validate_timestamp(start, DAY)
            validate_timestamp(end, DAY)
        case DATA_TYPES.HOUR:
            validate_timestamp(start, HOUR)
            validate_timestamp(end, HOUR)
        case DATA_TYPES.WEEK:
            validate_timestamp(start, WEEK)
            validate_timestamp(end, WEEK)
        case DATA_TYPES.MONTH:
            validate_timestamp(start, MONTH)
            validate_timestamp(end, MONTH)
        case DATA_TYPES.YEAR:
            validate_timestamp(start, YEAR)
            validate_timestamp(end, YEAR)
    if HOUR in data_type or DAY in data_type:
        start = f"{year}-{start}"
        end = f"{year}-{end}"
    return start, end, year
