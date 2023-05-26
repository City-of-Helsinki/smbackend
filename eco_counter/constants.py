import types

from django.conf import settings

from mobility_data.importers.utils import get_root_dir

INDEX_COLUMN_NAME = "startTime"

TRAFFIC_COUNTER_START_YEAR = 2015
# Manually define the end year, as the source data comes from the page
# defined in env variable TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL.
# Change end year when data for the next year is available.
TRAFFIC_COUNTER_END_YEAR = 2023
ECO_COUNTER_START_YEAR = 2020
LAM_COUNTER_START_YEAR = 2010
TELRAAM_COUNTER_START_YEAR = 2023


TRAFFIC_COUNTER = "TC"
ECO_COUNTER = "EC"
LAM_COUNTER = "LC"
TELRAAM_COUNTER = "TR"
TELRAAM_CSV = "TV"

COUNTERS = types.SimpleNamespace()
COUNTERS.TRAFFIC_COUNTER = TRAFFIC_COUNTER
COUNTERS.ECO_COUNTER = ECO_COUNTER
COUNTERS.LAM_COUNTER = LAM_COUNTER
COUNTERS.TELRAAM_COUNTER = TELRAAM_COUNTER

CSV_DATA_SOURCES = (
    (TRAFFIC_COUNTER, "TrafficCounter"),
    (ECO_COUNTER, "EcoCounter"),
    (LAM_COUNTER, "LamCounter"),
    (TELRAAM_COUNTER, "TelraamCounter"),
    (TELRAAM_CSV, "TelraamCSV"),
)
COUNTER_START_YEARS = {
    ECO_COUNTER: ECO_COUNTER_START_YEAR,
    TRAFFIC_COUNTER: TRAFFIC_COUNTER_START_YEAR,
    LAM_COUNTER: LAM_COUNTER_START_YEAR,
    TELRAAM_COUNTER: TELRAAM_COUNTER_START_YEAR,
}

TRAFFIC_COUNTER_METADATA_GEOJSON = "traffic_counter_metadata.geojson"
# LAM stations located in the municipalities list are included.
LAM_STATION_MUNICIPALITIES = ["Turku", "Raisio", "Kaarina", "Lieto"]

LAM_STATIONS_API_FETCH_URL = (
    settings.LAM_COUNTER_API_BASE_URL
    + "?api=liikennemaara&tyyppi=h&pvm={start_date}&loppu={end_date}"
    + "&lam_type=option1&piste={id}&luokka=kaikki&suunta={direction}&sisallytakaistat=0"
)
# Maps the direction of the traffic of station, (P)oispäin or (K)eskustaan päin)
LAM_STATIONS_DIRECTION_MAPPINGS = {
    "1_Piikkiö": "P",
    "1_Naantali": "P",
    "2_Naantali": "K",
    "1_Turku": "K",
    "2_Turku": "K",
    "2_Helsinki": "P",
    "1_Suikkila.": "K",
    "2_Artukainen.": "P",
    "1_Vaasa": "P",
    "1_Kuusisto": "P",
    "2_Kaarina": "K",
    "1_Tampere": "P",
    "1_Hämeenlinna": "P",
}

keys = [k for k in range(TRAFFIC_COUNTER_START_YEAR, TRAFFIC_COUNTER_END_YEAR + 1)]
# Create a dict where the years to be importer are keys and the value is the url of the csv data.
# e.g. {2015, "https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq/2015_laskenta_juha.csv"}
TRAFFIC_COUNTER_CSV_URLS = dict(
    [
        (k, f"{settings.TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL}{k}_laskenta_juha.csv")
        for k in keys
    ]
)
TELRAAM_COUNTER_API_BASE_URL = "https://telraam-api.net"
# Maximum 3 months at a time
TELRAAM_COUNTER_TRAFFIC_URL = f"{TELRAAM_COUNTER_API_BASE_URL}/v1/reports/traffic"
TELRAAM_COUNTER_AVAILABLE_CAMERAS_URL = f"{TELRAAM_COUNTER_API_BASE_URL}/v1/cameras"
TELRAAM_COUNTER_CAMERAS_URL = TELRAAM_COUNTER_API_BASE_URL + "/v1/cameras/{mac_id}"

TELRAAM_COUNTER_CAMERA_SEGMENTS_URL = (
    TELRAAM_COUNTER_API_BASE_URL + "/v1/segments/id/{id}"
)
# The start month of the start year as telraam data is not available
# from the beginning of the start tear
TELRAAM_COUNTER_START_MONTH = 5
TELRAAM_COUNTER_API_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TELRAAM_COUNTER_CSV_FILE_PATH = f"{get_root_dir()}/media/telraam_data/"
TELRAAM_COUNTER_CSV_FILE = (
    TELRAAM_COUNTER_CSV_FILE_PATH + "telraam_data_{id}_{day}_{month}_{year}.csv"
)
TELRAAM_COUNTER_CAMERAS = {
    # Mac id: Direction flag
    350457790598039: False,  # Kristiinanankatu, Joelle katsottaessa vasemmalle
}
