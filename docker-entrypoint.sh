#!/bin/bash
set -e

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
    ./scripts/run_imports.sh "$@"
fi
