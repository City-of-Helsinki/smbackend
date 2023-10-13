import types

from drf_spectacular.utils import OpenApiParameter

from environment_data.constants import VALID_DATA_TYPE_CHOICES

DATA_TYPES = types.SimpleNamespace()
HOUR = "hour"
DAY = "day"
WEEK = "week"
MONTH = "month"
YEAR = "year"
DATA_TYPES.HOUR = HOUR
DATA_TYPES.DAY = DAY
DATA_TYPES.WEEK = WEEK
DATA_TYPES.MONTH = MONTH
DATA_TYPES.YEAR = YEAR
DATETIME_FORMATS = {
    HOUR: "%m-%d",
    DAY: "%m-%d",
    WEEK: "%W",
    MONTH: "%m",
    YEAR: "%Y",
}

YEAR_PARAM = OpenApiParameter(
    name="year",
    location=OpenApiParameter.QUERY,
    description=("Year of the data, not required when retrieving year data."),
    required=False,
    type=int,
)
TYPE_PARAM = OpenApiParameter(
    name="type",
    location=OpenApiParameter.QUERY,
    description=(
        f"Type of the data to be returned, types are: {', '.join([f for f in DATETIME_FORMATS])}"
    ),
    required=True,
    type=str,
)
TIME_FORMATS_STR = ", ".join([f"{f[0]}: {f[1]}" for f in DATETIME_FORMATS.items()])
START_PARAM = OpenApiParameter(
    name="start",
    location=OpenApiParameter.QUERY,
    description=(
        f"Start of the interval. Formats for different types are: {TIME_FORMATS_STR}"
    ),
    required=True,
    type=str,
)
END_PARAM = OpenApiParameter(
    name="end",
    location=OpenApiParameter.QUERY,
    description=(
        f"End of the interval. Formats for different types are: {TIME_FORMATS_STR}"
    ),
    required=True,
    type=str,
)
STATION_PARAM = OpenApiParameter(
    name="station_id",
    location=OpenApiParameter.QUERY,
    description=("Id of the environemnt data station"),
    required=True,
    type=str,
)

DATA_TYPE_PARAM = OpenApiParameter(
    name="data_type",
    location=OpenApiParameter.QUERY,
    description=(
        f"'data_type' of the station, valid types are: {VALID_DATA_TYPE_CHOICES}"
    ),
    required=False,
    type=str,
)


ENVIRONMENT_DATA_PARAMS = [
    TYPE_PARAM,
    YEAR_PARAM,
    START_PARAM,
    END_PARAM,
    STATION_PARAM,
]
ENVIRONMENT_STATION_PARAMS = [
    DATA_TYPE_PARAM,
]
