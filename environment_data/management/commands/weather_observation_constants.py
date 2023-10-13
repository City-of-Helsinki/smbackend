# Note, change to 2010
START_YEAR = 2022
STATION_MATCH_STRINGS = ["Automaattinen sääasema"]
TEMPERATURE = "Temperature"
PRECIPITATIONAMOUNT = "PrecipitationAmount"
HUMINIDITY = "Humidity"
PRESSURE = "Pressure"
WINDDIRETION = "WindDirection"
WINDSPEEDMS = "WindSpeedMS"
OBSERVABLE_PARAMETERS = [
    TEMPERATURE,
    PRECIPITATIONAMOUNT,
    HUMINIDITY,
    PRESSURE,
    WINDDIRETION,
    WINDSPEEDMS,
]
PARAMS = {
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
https://opendata.fmi.fi/wfs/fin?service=WFS&version=2.0.0&request=GetFeature&storedquery_id=
fmi::observations::weather::hourly::timevaluepair&fmisid=100949&timestep=60&parameters=
Temperature,pressure&startTime=2023-10-9T00:00:00Z&endTime=2023-10-10T23:00:00Z
-100908
https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=describeStoredQueries&
Pressure,GeopHeight,Temperature,DewPoint,Humidity,WindDirection, WindSpeedMS,WindUMS,
WindVMS,PrecipitationAmount,TotalCloudCover,LowCloudCover, MediumCloudCover,HighCloudCover,
RadiationGlobal,RadiationGlobalAccumulation, RadiationNetSurfaceLWAccumulation,RadiationNetSurfaceSWAccumulation,
 RadiationSWAccumulation,Visibility,WindGust,Cape
"""
