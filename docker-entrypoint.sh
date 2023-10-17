#!/bin/bash
set -e

if [[ "$APPLY_MIGRATIONS" = "True" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi

if [ "$1" = 'start_django_development_server' ]; then
    until nc -z -v -w30 postgres 5432
    do
      echo "Waiting for the database..."
      sleep 1
    done
    echo "Database is up!"
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
    exec uwsgi --plugin http,python3 --master --http :8000 \
               --processes 4 --threads 1 \
               --need-app \
               --mount ${URL_PREFIX:-/}=smbackend/wsgi.py \
               --manage-script-name \
               --die-on-term \
               --strict \
               --ignore-sigpipe \
               --ignore-write-errors \
               --disable-write-exception \
               --reload-on-rss 500
fi
