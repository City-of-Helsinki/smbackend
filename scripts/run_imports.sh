#!/bin/bash

export PYTHONIOENCODING=utf-8

function stage_0 {
    # Very seldomly executed imports (once a year)
    # Finnish municipalities
    ./manage.py geo_import finland --municipalities
}

function stage_1 {
    # Somewhat rarely executed imports (once a month)
    # Parking areas update
    ./manage.py update_parking_areas
}

function stage_2 {
    # Once a day
    # Helsinki, Espoo and HSY administrative division and address data
    ./manage.py geo_import helsinki --divisions
    ./manage.py geo_import espoo --divisions
    ./manage.py geo_import hsy --divisions
    ./manage.py geo_import helsinki --addresses
    # Unit properties import
    ./manage.py services_import_v4 unit_properties
}

function stage_3 {
    # Frequently executed imports (every 30m)
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
