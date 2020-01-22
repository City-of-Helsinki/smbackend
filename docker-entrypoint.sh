#!/bin/bash
set -e

echo "Checking for database on host 'postgres', port 5432"
until nc -z -v -w30 postgres 5432
do
  echo "Waiting for postgres database connection..."
  sleep 1
done
echo "Database found!"

if [[ "$APPLY_MIGRATIONS" = "true" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi

if [ "$1" = 'start_uwsgi_production_server' ]; then
    # Start server
    echo "Starting server"
    ./deploy/server.sh

elif [ "$1" = 'start_django_development_server' ]; then
    # Start server
    echo "Starting server"
    python manage.py runserver 0.0.0.0:8000

elif [ "$1" = 'maintenance_tasks' ]; then
    shift
    ./scripts/maintenance_tasks.sh "$@"
fi
