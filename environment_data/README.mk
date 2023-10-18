# Environment data APP
The APP imports, processes and servers history data of the environment.
Hour datas are store as they are in the source data. Day, week, month and year
datas are stored as means, except from the Precipitation amount parameters where the
cumulative value is calculated.

## AQ (Air Quality) 
The imported parameters are:
* AQINDEX_PT1H_avg "Air quality index" (Ilmanlaatuindeksi)
* SO2_PT1H_avg "Sulphur dioxide - ug/m3" (Rikkidioksiidi)
* O3_PT1H_avg "Ozone - ug/m3" (Otsooni)
* NO2_PT1H_avg "Nitrogen dioxide - ug/m3" (Typpidioksiidi)
* PM10_PT1H_avg "Particulate matter < 10 µm - ug/m3" (Hengitettävät hiukkaset)
* PM25_PT1H_avg "Particulate matter < 2.5 µm - ug/m3" (Pienhiukkaset)

## WO (Weather Observation)
The imported parameters are:
* TA_PT1H_AVG "Air temperature - degC"
* RH_PT1H_AVG "Relative humidity - %"
* WS_PT1H_AVG "Wind speed - m/s"
* WD_PT1H_AVG "Wind direction - deg"
* PRA_PT1H_ACC "Precipitation amount - mm", Note, Cumulative value
* PA_PT1H_AVG "Air pressure - hPA"

# Importing
## Initial import
Note, initial import deletes all previously imported data for the given data type.
E.g., to initial import data and stations for weather observations:
```
./manage.py import_environment_data --initial-import-with-stations WO
```
E.g., to initial import air quality data without deleting stations:
```
./manage.py import_environment_data --initial-import AQ
```

## Incremental import
E.e., to incrementally import air quality data type:
```
./manage.py import_environment_data --data-types AQ
```

## To delete all data
```
./manage.py delete_all_environment_data
```


