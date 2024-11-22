# Eco-counter Turku Importer

Imports/Processes data from:
https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq 
Imports both "Liikennelasketa-Ilmaisintiedot 15 min aikaväleillä"(Traffic Counter) and "Eco-Counter" (Eco Counter) datas. Imports/processes "LAM-Counter" (LAM Counter) data from https://www.digitraffic.fi/tieliikenne/lam/ and
Telraam data from https://telraam-api.net/.

## Installation:
Add following lines to the .env:
ECO_COUNTER_OBSERVATIONS_URL=https://data.turku.fi/cjtv3brqr7gectdv7rfttc/counters-15min.csv
TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL=https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq/
LAM_COUNTER_STATIONS_URL=https://tie.digitraffic.fi/api/v3/metadata/tms-stations
LAM_COUNTER_API_BASE_URL=https://tie-lam-test.digitraffic.fi
Note, The urls can change. Up-to-date urls can be found at:
https://www.avoindata.fi/data/fi/dataset/turun-seudun-liikennemaaria
and
https://www.digitraffic.fi/tieliikenne/lam/
Telraam API token, required when fetching Telraam data to csv (import_telraam_to_csv.py) https://telraam.helpspace-docs.io/article/27/you-wish-more-data-and-statistics-telraam-api
TELRAAM_TOKEN=

## Importing

### Initial Import
The initial import, this must be done before starting with the continous incremental imports:
./manage.py import_counter_data --init COUNTERS
e.g. ./manage.py import_counter_data --init EC TC
The counters are EC(Eco Counter), TC(Traffic Counter), LC(Lam Counter) and TR(Telraam Counter).

### Continous Import
For continous (hourly) imports run:
./manage.py import_counter_data --counters COUNTERS
e.g. ./manage.py import_counter_data --counters EC TC
Counter names are: EC (Eco Counter), TC (Traffic Counter), LC (Lam Counter) and TR (Telraam Counter).
Note, Traffic Counter data is updated once a week and Lam Counter data once a day.

## Deleting data
To delete data use the delete_counter_data management command.
e.g. to delete all Lam Counter data type:
```
./manage.py delete_counter_data --counters LC
```

### Importing Telraam raw data
In order to import Telraam data into the database the raw data has to be imported. The raw data is imported with the _import_telraam_to_csv_ management command.
The imported should be set to be run once a hour (see: https://github.com/City-of-Turku/smbackend/wiki/Celery-Tasks#telraam-to-csv-eco_countertasksimport_telraam_to_csv )
Telraam raw data is imported to PROJECT_ROOT/media/telraam_data/. 

## Troubleshooting
For reasons unknown, the amount of sensors can sometimes change in the source csv file, e.g. the amount of columns changes. If this happens, run the initial import: ./manage.py import_counter_data --init and after that it is safe to run the importer as normal.

## Testing
If changes are made to the importer, run tests that verifies the correctness with:
pytest -m test_import_counter_data

