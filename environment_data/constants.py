import types

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

AIR_QUALITY = "AQ"
WEATHER_OBSERVATION = "WO"
DATA_TYPES_FULL_NAME = {
    AIR_QUALITY: "Air Quality",
    WEATHER_OBSERVATION: "Weather Observation",
}
DATA_TYPE_CHOICES = (
    (AIR_QUALITY, DATA_TYPES_FULL_NAME[AIR_QUALITY]),
    (WEATHER_OBSERVATION, DATA_TYPES_FULL_NAME[WEATHER_OBSERVATION]),
)

DATA_TYPES = types.SimpleNamespace()
DATA_TYPES.AIR_QUALITY = AIR_QUALITY
DATA_TYPES.WEATHER_OBSERVATION = WEATHER_OBSERVATION

VALID_DATA_TYPE_CHOICES = ", ".join(
    [item[0] + f" ({item[1]})" for item in DATA_TYPES_FULL_NAME.items()]
)
DATA_TYPES_LIST = [AIR_QUALITY, WEATHER_OBSERVATION]

retry_strategy = Retry(
    total=10,
    status_forcelist=[429],
    allowed_methods=["GET", "POST"],
    backoff_factor=30,  # 30, 60, 120 , 240, ..seconds
)
adapter = HTTPAdapter(max_retries=retry_strategy)
REQUEST_SESSION = requests.Session()
REQUEST_SESSION.mount("https://", adapter)
REQUEST_SESSION.mount("http://", adapter)
