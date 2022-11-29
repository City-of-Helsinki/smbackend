# Eco-counter Turku Importer

Imports/Processes data from:
https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq 
Imports both "Liikennelasketa-Ilmaisintiedot 15 min aikaväleillä"(Traffic Counter) and "Eco-Counter" (Eco Counter) datas. Imports/processes "LAM-Counter" (LAM Counter) data from https://www.digitraffic.fi/tieliikenne/lam/


## Installation:
Add following lines to the .env:
ECO_COUNTER_STATIONS_URL=https://dev.turku.fi/datasets/ecocounter/liikennelaskimet.geojson
ECO_COUNTER_OBSERVATIONS_URL=https://data.turku.fi/cjtv3brqr7gectdv7rfttc/counters-15min.csv
TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL=https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq/
LAM_COUNTER_STATIONS_URL=https://tie.digitraffic.fi/api/v3/metadata/tms-stations
LAM_COUNTER_API_BASE_URL=https://tie-lam-test.digitraffic.fi
Note, The urls can change. Up-to-date urls can be found at:
https://www.avoindata.fi/data/fi/dataset/turun-seudun-liikennemaaria
and
https://www.digitraffic.fi/tieliikenne/lam/

## Importing

### Initial Import
The initial import, this must be done before starting with the continous incremental imports:
./manage.py import_counter_data --init COUNTERS
e.g. ./manage.py import_counter_data --init EC TC
The counters are EC(Eco Counter), TC(Traffic Counter) and LC(Lam Counter).

### Continous Import
For continous (hourly) imports run:
./manage.py import_counter_data --counters COUNTERS
e.g. ./manage.py import_counter_data --counters EC TC
Counter names are: EC (Eco Counter), TC (Traffic Counter) and LC (Lam Counter).
Note, Traffic Counter data is updated once a week.

## Troubleshooting
For reasons unknown, the amount of sensors can sometimes change in the source csv file, e.g. the amount of columns changes. If this happens, run the initial import: ./manage.py import_counter_data --init and after that it is safe to run the importer as normal.

## Testing
If changes are made to the importer, run tests that verifies the correctness with:
pytest -m test_import_counter_data

