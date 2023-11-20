from datetime import datetime

from rest_framework.exceptions import ParseError

from .constants import DATA_TYPES, DATETIME_FORMATS, DAY, HOUR, MONTH, WEEK, YEAR


def validate_timestamp(timestamp_str, data_type):
    time_format = DATETIME_FORMATS[data_type]
    try:
        datetime.strptime(timestamp_str, time_format)
    except ValueError:
        return f"{timestamp_str} invalid format date format, valid format for type {data_type} is {time_format}"
    return None


def get_start_and_end_and_year(filters, data_type):
    start = filters.get("start", None)
    end = filters.get("end", None)
    year = filters.get("year", None)

    if not start or not end:
        raise ParseError("Supply both 'start' and 'end' parameters")

    if YEAR not in data_type and not year:
        raise ParseError("Supply 'year' parameter")

    res1 = None
    res2 = None
    match data_type:
        case DATA_TYPES.DAY:
            res1 = validate_timestamp(start, DAY)
            res2 = validate_timestamp(end, DAY)
        case DATA_TYPES.HOUR:
            res1 = validate_timestamp(start, HOUR)
            res2 = validate_timestamp(end, HOUR)
        case DATA_TYPES.WEEK:
            res1 = validate_timestamp(start, WEEK)
            res2 = validate_timestamp(end, WEEK)
        case DATA_TYPES.MONTH:
            res1 = validate_timestamp(start, MONTH)
            res2 = validate_timestamp(end, MONTH)
        case DATA_TYPES.YEAR:
            res1 = validate_timestamp(start, YEAR)
            res2 = validate_timestamp(end, YEAR)

    if res1:
        raise ParseError(res1)
    if res2:
        raise ParseError(res2)

    if HOUR in data_type or DAY in data_type:
        start = f"{year}-{start}"
        end = f"{year}-{end}"
    return start, end, year
