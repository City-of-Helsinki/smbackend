import platform
import types
from datetime import datetime

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

INDEX_COLUMN_NAME = "startTime"

TRAFFIC_COUNTER_START_YEAR = 2015
# Manually define the end year, as the source data comes from the page
# defined in env variable TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL.
# Change end year when data for the next year is available.
TRAFFIC_COUNTER_END_YEAR = datetime.today().year
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

COUNTERS_LIST = [ECO_COUNTER, TRAFFIC_COUNTER, LAM_COUNTER, TELRAAM_COUNTER]
COUNTER_CHOICES_STR = (
    f"{ECO_COUNTER}, {TRAFFIC_COUNTER}, {TELRAAM_COUNTER} and {LAM_COUNTER}"
)
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
ECO_COUNTER_STATIONS_GEOJSON = "eco_counter_stations.geojson"
LAM_STATIONS_API_FETCH_URL = (
    settings.LAM_COUNTER_API_BASE_URL
    + "?api=liikennemaara&tyyppi=h&pvm={start_date}&loppu={end_date}"
    + "&lam_type=option1&piste={id}&luokka=kaikki&suunta={direction}&sisallytakaistat=0"
)
# LAM stations in the locations list are included.
LAM_STATION_LOCATIONS = ["Turku", "Raisio", "Kaarina", "Lieto", "Hauninen", "Oriketo"]
# Header that is added to the request that fetches the LAM data.
LAM_STATION_USER_HEADER = {
    "Digitraffic-User": f"{platform.uname()[1]}/Turun Palvelukartta"
}
# Mappings are derived by the 'suunta' and  the 'suuntaselite' columns in the source data.
# (P)oispäin or (K)eskustaan päin)
LAM_STATIONS_DIRECTION_MAPPINGS = {
    # vt8_Raisio
    "1_Vaasa": "P",
    "2_Turku": "K",
    # vt1_Kaarina_Kirismäki
    "1_Turku": "K",
    "2_Helsinki": "P",
    # vt10_Lieto
    "1_Hämeenlinna": "P",
    # "2_Turku": "K", Duplicate
    # vt1_Turku_Kupittaa
    # "1_Turku" Duplicate
    # "2_Helsinki" Duplicate
    # vt1_Turku_Kurkela_länsi
    # "1_Turku" Duplicate
    # "2_Helsinki" Duplicate
    # vt1_Kaarina_Kurkela_itä
    # "1_Turku" Duplicate
    # "2_Helsinki" Duplicate
    # vt1_Kaarina
    # "1_Turku" Duplicate
    # "2_Helsinki" Duplicate
    # vt1_Kaarina_Piikkiö
    # "1_Turku" Duplicate
    # "2_Helsinki" Duplicate
    # yt1851_Turku_Härkämäki
    "1_Suikkila": "K",
    "2_Artukainen": "P",
    # kt40_Hauninen
    "1_Piikkiö": "K",
    "2_Naantali": "P",
    # kt40_Oriketo
    # "1_Piikkiö": "K", duplicate
    # "2_Naantali": "P", dupicate
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
TELRAAM_COUNTER_CAMERAS_URL = TELRAAM_COUNTER_API_BASE_URL + "/v1/cameras/{mac_id}"

TELRAAM_COUNTER_CAMERA_SEGMENTS_URL = (
    TELRAAM_COUNTER_API_BASE_URL + "/v1/segments/id/{id}"
)
# The start month of the start year as telraam data is not available
# from the beginning of the start tear
TELRAAM_COUNTER_START_MONTH = 5
TELRAAM_COUNTER_API_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TELRAAM_COUNTER_DATA_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

TELRAAM_COUNTER_CSV_FILE_PATH = f"{settings.MEDIA_ROOT}/telraam_data/"
TELRAAM_COUNTER_CSV_FILE = (
    TELRAAM_COUNTER_CSV_FILE_PATH + "telraam_data_{mac}_{year}_{month}_{day}.csv"
)
TELRAAM_STATION_350457790598039 = 350457790598039
TELRAAM_STATION_350457790600975 = 350457790600975
TELRAAM_COUNTER_CAMERAS = {
    # Mac id: Direction flag (True=rgt prefix will be keskustaan päin)
    TELRAAM_STATION_350457790598039: False,  # Kristiinanankatu, Joelle katsottaessa vasemmalle
    TELRAAM_STATION_350457790600975: True,  # Kristiinanankatu, Joelle katsottaessa oikealle
}
# For 429 (too many request) TELRAAM need a retry strategy
retry_strategy = Retry(
    total=10,
    status_forcelist=[429],
    allowed_methods=["GET", "POST"],
    backoff_factor=30,  # 30, 60, 120 , 240, ..seconds
)
adapter = HTTPAdapter(max_retries=retry_strategy)
TELRAAM_HTTP = requests.Session()
TELRAAM_HTTP.mount("https://", adapter)
TELRAAM_HTTP.mount("http://", adapter)


# Telraam stations initial geometries in WKT format
# These coordinates are used if CSV files do not include any geometries.
TELRAAM_STATIONS_INITIAL_WKT_GEOMETRIES = {
    TELRAAM_STATION_350457790598039: {
        "location": "POINT (239628.47846388057 6710757.471557152)",
        "geometry": "MULTILINESTRING ((239565.80107971327 6710861.8209667895, 239572.58901459936 6710850.524818219,"
        " 239574.73294378238 6710846.950531884, 239628.47846388057 6710757.471557152,"
        " 239630.0339247121 6710754.923177836, 239635.52748551324 6710745.732077925))",
    },
    TELRAAM_STATION_350457790600975: {
        "location": "POINT (239523.2288977413 6710932.715108742)",
        "geometry": "MULTILINESTRING ((239490.42663459244 6710989.092283992, 239493.45037993207 6710983.7110835295,"
        " 239495.88642941663 6710979.3668986475, 239517.9904128411 6710941.530425406,"
        " 239520.0691194288 6710937.971973339, 239523.2288977413 6710932.715108742,"
        " 239529.37000273907 6710922.482472116, 239558.08254550528 6710874.681753734,"
        " 239559.97438753376 6710871.516775628, 239565.80107971327 6710861.8209667895))",
    },
}
