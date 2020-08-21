#!/bin/bash

% export PYTHONIOENCODING=utf-8
set -e

TIMESTAMP_FORMAT="+%Y-%m-%d %H:%M:%S"
ROOT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -f $ROOT_PATH/local_update_config ]; then
    $ROOT_PATH/local_update_config
fi

echo ---------------------------------
echo "$(date "$TIMESTAMP_FORMAT") Importing observation initial data"
echo ---------------------------------

cd $ROOT_PATH

timeout 20m nice python manage.py loaddata observations/fixtures/maintenance_users.yaml 2>&1
timeout 20m nice python manage.py loaddata observations/fixtures/initial_observable_properties_common.yaml 2>&1
timeout 20m nice python manage.py loaddata observations/fixtures/initial_observable_properties_skating.yaml 2>&1
timeout 20m nice python manage.py loaddata observations/fixtures/initial_observable_properties_skiing.yaml 2>&1
timeout 20m nice python manage.py loaddata observations/fixtures/initial_observable_properties_swimming.yaml 2>&1

echo ---------------------------------
echo "$(date "$TIMESTAMP_FORMAT") Observation initial data imported successfully"
echo ---------------------------------
