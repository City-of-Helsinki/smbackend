#!/bin/bash

export PYTHONIOENCODING=utf-8

function stage_0 {
    # Execute every 6 months
    # Finnish municipalities
    ./manage.py geo_import finland --municipalities
    # Statistical districts
    ./manage.py update_statistical_districts
}

function stage_1 {
    # Execute once a week
    # Import Helsinki, Espoo and HSY administrative divisions,
    # addresses, parking areas, parking payzones and nature reserves.
    # Additionally, index search columns for a better performance.
    ./manage.py geo_import espoo --divisions
    GDAL_HTTP_UNSAFESSL=YES ./manage.py geo_import hsy --divisions
    ./manage.py geo_import helsinki --addresses
    ./manage.py geo_import uusimaa --addresses
    ./manage.py update_parking_areas
    ./manage.py update_vantaa_parking_areas
    ./manage.py update_vantaa_parking_payzones
    ./manage.py update_vantaa_nature_reserves
    ./manage.py index_search_columns
}

function stage_2 {
    # Execute daily
    # Unit properties import
    ./manage.py services_import_v4 unit_properties
    ./manage.py update_helsinki_school_districts school
    ./manage.py update_helsinki_school_districts preschool
    ./manage.py verify_school_districts
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
