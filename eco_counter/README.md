# Eco-counter Turku Importer

## Installation:
Add following lines to the .env:
ECO_COUNTER_STATIONS_URL=https://dev.turku.fi/datasets/ecocounter/liikennelaskimet.geojson
ECO_COUNTER_OBSERVATIONS_URL=https://data.turku.fi/cjtv3brqr7gectdv7rfttc/counters-15min.csv
Note, THe urls can change. Up-to-date urls can be found at:
https://www.avoindata.fi/data/fi/dataset/turun-seudun-liikennemaaria

## Importing

The initial import, this must be done before starting with the continous incremental imports:
./manage.py import_eco_counter --init

For continous (hourly) imports run:
./manage.py import_eco_counter


## Troubleshooting

For reasons unknown, the amount of sensors can sometimes change in the source csv file, e.g. the amount of columns changes. If this happens, run the initial import: ./manage.py import_eco_counter --init and after that is safe to run the importer as normal.


## Testing
If changes are made to the importer, run tests that verifies the correctness with:
pytest -m test_import_eco_counter

