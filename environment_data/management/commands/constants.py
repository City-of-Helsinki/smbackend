from .weather_observation_constants import PRECIPITATION_AMOUNT

# If param is defined as cumulative, sum() function is used for DataFrame insted for mean()
CUMULATIVE_PARAMETERS = [PRECIPITATION_AMOUNT]
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SOURCE_DATA_SRID = 4326

NAMESPACES = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "om": "http://www.opengis.net/om/2.0",
    "omso": "http://inspire.ec.europa.eu/schemas/omso/3.0",
    "sams": "http://www.opengis.net/samplingSpatial/2.0",
    "wml2": "http://www.opengis.net/waterml/2.0",
    "ef": "http://inspire.ec.europa.eu/schemas/ef/4.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "gml": "http://www.opengis.net/gml/3.2",
}

STATION_URL = (
    "https://opendata.fmi.fi/wfs/fin?service=WFS&version=2.0.0&request=GetFeature&storedquery_id=fmi::ef::stations"
    "&startTime=2023-10-9T00:00:00Z&endTime=2023-10-10T23:00:00Z"
)
DATA_URL = "https://data.fmi.fi/fmi-apikey/0fe6aa7c-de21-4f68-81d0-ed49c0409295/wfs"
