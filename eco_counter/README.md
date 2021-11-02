# Eco-counter Turku

## Installation:
Add following lines to .env:
ECO_COUNTER_STATIONS_URL=https://dev.turku.fi/datasets/ecocounter/liikennelaskimet.geojson
ECO_COUNTER_OBSERVATIONS_URL=https://data.turku.fi/cjtv3brqr7gectdv7rfttc/counters-15min.csv

Note, THe URLs can change. Up to date urls can be found at:
https://www.avoindata.fi/data/fi/dataset/turun-seudun-liikennemaaria

## Importing

The initial import or if the observation stations has changed. 
./manage.py import_eco_counter --init

For continious (hourly) imports run
./manage.py import_eco_counter