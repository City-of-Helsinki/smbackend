#!/bin/bash

function stage_0 {
    # Very seldomly executed imports (once a year max)
    # Finnish municipalities in munigeo
    ./manage.py geo_import finland --municipalities
}

function stage_1 {
    # Somewhat rarely executed imports (once a month max)
    # Helsinki administrative division munigeo data
    ./manage.py geo_import helsinki --divisions
}

function stage_2 {
    # Once a day?
    ./manage.py geo_import helsinki --addresses
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

