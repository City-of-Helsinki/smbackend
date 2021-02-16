#!/bin/bash
set -e

if [[ "$APPLY_MIGRATIONS" = "true" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi

if [ "$1" = 'start_django_development_server' ]; then
    # Start server
    echo "Starting development server"
    ./manage.py runserver 0.0.0.0:8000

elif [ "$1" = 'maintenance_tasks' ]; then
    shift
    ./scripts/run_imports.sh "$@"
elif [ "$1" ]; then
    echo "Running command: $1"
    $1
else
    exec uwsgi --plugin http,python3 --master --http :8000 --need-app --wsgi-file deploy/wsgi.py \
               --static-map ${STATIC_URL:-/static}=${STATIC_ROOT:-/srv/smbackend/static} \
               --processes 4 --threads 1 \
               --die-on-term
fi
