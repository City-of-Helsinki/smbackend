START_YEAR = 2010
# NOTE, No more than 10000 hours is allowed per request.
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
STATION_MATCH_STRINGS = ["Kolmannen osapuolen ilmanlaadun havaintoasema"]
