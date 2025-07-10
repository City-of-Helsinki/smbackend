#!/bin/bash

set -e

# Wait for the database to be available
if [ -z "$SKIP_DATABASE_CHECK" ] || [ "$SKIP_DATABASE_CHECK" = "0" ]; then
  until nc -z -v -w30 "$DATABASE_HOST" "${DATABASE_PORT:-5432}"
  do
    echo "Waiting for postgres database connection..."
    sleep 1
  done
  echo "Database is up!"
fi

if [[ "$APPLY_MIGRATIONS" = "True" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi

if [[ "$COMPILE_TRANSLATIONS" = "True" ]]; then
    echo "Compile translations..."
    ./manage.py compilemessages
fi

# Start server
if [ "$1" = 'maintenance_tasks' ]; then
    shift
    ./scripts/run_imports.sh "$@"
elif [[ -n "$*" ]]; then
    echo "Running command: $*"
    "$@"
elif [[ "$DEV_SERVER" = "True" ]]; then
    python -Wd ./manage.py runserver 0.0.0.0:8000
else
    export UWSGI_PROCESSES=${UWSGI_PROCESSES:-4}
    uwsgi --ini .prod/uwsgi.ini
fi
