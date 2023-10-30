START_YEAR = 2010
# NOTE, No more than 10000 hours is allowed per request.
AIR_QUALITY_INDEX = "AQINDEX_PT1H_avg"  # Ilmanlaatuindeksi
PARTICULATE_MATTER_10 = "PM10_PT1H_avg"  # Hengitettävät hiukkaset
SULPHUR_DIOXIDE = "SO2_PT1H_avg"  # rikkidioksiidi
OZONE = "O3_PT1H_avg"  # otsooni
PARTICULATE_MATTER_25 = "PM25_PT1H_avg"  # pienhiukkaset
NITROGEN_DIOXIDE = "NO2_PT1H_avg"  # typpidioksiidi

OBSERVABLE_PARAMETERS = [
    AIR_QUALITY_INDEX,
    PARTICULATE_MATTER_10,
    SULPHUR_DIOXIDE,
    OZONE,
    PARTICULATE_MATTER_25,
    NITROGEN_DIOXIDE,
]
PARAMETER_DESCRIPTIONS = {
    AIR_QUALITY_INDEX: "Air quality index",
    SULPHUR_DIOXIDE: "Sulphur dioxide - ug/m3",
    NITROGEN_DIOXIDE: "Nitrogen dioxide - ug/m3",
    OZONE: "Ozone - ug/m3",
    PARTICULATE_MATTER_10: "Particulate matter < 10 µm - ug/m3",
    PARTICULATE_MATTER_25: "Particulate matter < 2.5 µm - ug/m3",
}


REQUEST_PARAMS = {
    "request": "getFeature",
    "storedquery_id": "urban::observations::airquality::hourly::timevaluepair",
    "geoId": None,
    "parameters": None,
    "who": "fmi",
    "startTime": None,
    "endTime": None,
}
STATION_MATCH_STRINGS = ["Kolmannen osapuolen ilmanlaadun havaintoasema"]
