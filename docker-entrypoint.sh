#!/bin/bash
set -e
if [[ "$APPLY_MIGRATIONS" = "true" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi

if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "Creating superuser if it does not exists."
    python manage.py ensure_adminuser --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL \
        --password $DJANGO_SUPERUSER_PASSWORD
fi

if [ "$1" = 'start_django_development_server' ]; then
    # Start server
    echo "Starting development server."
    ./manage.py runserver 0.0.0.0:8000

elif [ "$1" = 'maintenance_tasks' ]; then
    shift
    ./scripts/run_imports.sh "$@"
elif [ "$1" ]; then
    echo "Running command: $1"
    $1
else
    exec uwsgi --plugin http,python3 --master --http :8000 \
               --processes 4 --threads 1 \
               --need-app \
               --mount ${URL_PREFIX:-/}=smbackend/wsgi.py \
               --manage-script-name \
               --die-on-term \
               --strict
fi
