# Note, change to 2010
START_YEAR = 2022
STATION_MATCH_STRINGS = ["Automaattinen sääasema"]
AIR_TEMPERATURE = "TA_PT1H_AVG"
RELATIVE_HUMIDITY = "RH_PT1H_AVG"
WIND_SPEED = "WS_PT1H_AVG"
WIND_DIRECTION = "WD_PT1H_AVG"
PRECIPITATION_AMOUNT = "PRA_PT1H_ACC"
AIR_PRESSURE = ""

OBSERVABLE_PARAMETERS = [AIR_TEMPERATURE, RELATIVE_HUMIDITY, WIND_SPEED]
PARAMETER_DESCRIPTIONS = {
    AIR_TEMPERATURE: "Air temperature - degC",
    RELATIVE_HUMIDITY: "Relative humidity - %",
    WIND_SPEED: "Wind speed - m/s",
    WIND_DIRECTION: "Wind direction - deg",
    PRECIPITATION_AMOUNT: "Precipitation amount - mm",
    AIR_PRESSURE: "Air pressure - hPA",
}
REQUEST_PARAMS = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "getFeature",
    "storedquery_id": "fmi::observations::weather::hourly::timevaluepair",
    "fmisid": None,
    # "geoId": None,
    "parameters": None,
    "startTime": None,
    "endTime": None,
    "timeStep": 60,
}
DATA_URL = "https://opendata.fmi.fi/wfs"
"""
https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi%3A%3Aobservations%3A%3Aweather%3A%3Ahourly%3A%3Atimevaluepair&
fmisid=100908&startTime=2022-1-01T00%3A00Z&endTime=2022-1-31T23%3A00Z&timeStep=60
https://opendata.fmi.fi/meta?observableProperty=observation&param=TA_PT1H_MAX&language=eng
https://opendata.fmi.fi/meta?observableProperty=observation&param=WS_PT1H_MAX&language=eng
https://opendata.fmi.fi/meta?observableProperty=observation&param=TA_PT1H_MIN&language=eng
https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=describeStoredQueries&
Pressure,GeopHeight,Temperature,DewPoint,Humidity,WindDirection, WindSpeedMS,WindUMS,
WindVMS,PrecipitationAmount,TotalCloudCover,LowCloudCover, MediumCloudCover,HighCloudCover,
RadiationGlobal,RadiationGlobalAccumulation, RadiationNetSurfaceLWAccumulation,RadiationNetSurfaceSWAccumulation,
 RadiationSWAccumulation,Visibility,WindGust,Cape
"""
