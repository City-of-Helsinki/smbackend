#!/bin/bash

export PYTHONIOENCODING=utf-8

function stage_0 {
    # Very seldomly executed imports (once a year max)
    # Finnish municipalities in munigeo
    ./manage.py geo_import finland --municipalities
}

function stage_1 {
    # Somewhat rarely executed imports (once a month max)
    # Helsinki, Espoo and HSY administrative division munigeo data
    ./manage.py geo_import helsinki --divisions
    ./manage.py geo_import espoo --divisions
    ./manage.py geo_import hsy --divisions
    ./manage.py update_parking_areas
}

function stage_2 {
    # Once a day?
    ./manage.py geo_import helsinki --addresses
    ./manage.py services_import_v4 --traceback unit_properties
    ./manage.py lipas_import --muni-id=92 --muni-id=91 --muni-id=49 --muni-id=235 --muni-id=257
}

function stage_3 {
    # Frequently executed imports (once an hour at the least)
    # Toimipisterekisteri imports
    ./scripts/update.sh
}

function stage_all {
    next=0
    while stage_"$next"; do
        next=$((next+1))
    done
}

echo -n "Running imports "
while test $# -gt 0
do
    echo -n "$1 "
    stage_"$1"
    shift
done
echo
