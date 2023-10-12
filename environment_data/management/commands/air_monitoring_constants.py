START_YEAR = 2010
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

SOURCE_DATA_SRID = 4326

# NOTE, No more than 10000 hours is allowed per request.
DATA_URL = "https://data.fmi.fi/fmi-apikey/0fe6aa7c-de21-4f68-81d0-ed49c0409295/wfs"
AQINDEX_PT1H_AVG = "AQINDEX_PT1H_avg"  # Ilmanlaatuindeksi
PM10_PT1H_AVG = "PM10_PT1H_avg"  # Hengitettävät hiukkaset
SO2_PT1H_AVG = "SO2_PT1H_avg"  # rikkidioksiidi
O3_PT1H_avg = "O3_PT1H_avg"  # otsooni
PM25_PT1H_avg = "PM25_PT1H_avg"  # pienhiukkaset
NO2_PT1H_avg = "NO2_PT1H_avg"  # typpidioksiidi

OBSERVABLE_PARAMETERS = [
    AQINDEX_PT1H_AVG,
    PM10_PT1H_AVG,
    SO2_PT1H_AVG,
    O3_PT1H_avg,
    PM25_PT1H_avg,
    NO2_PT1H_avg,
]

PARAMS = {
    "request": "getFeature",
    "storedquery_id": "urban::observations::airquality::hourly::timevaluepair",
    "geoId": None,
    "parameters": None,
    "who": "fmi",
    "startTime": None,
    "endTime": None,
}
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
    "https://data.fmi.fi/fmi-apikey/0fe6aa7c-de21-4f68-81d0-ed49c0409295/"
    "wfs?request=getFeature&storedquery_id=fmi::ef::stations"
)
