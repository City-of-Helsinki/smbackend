#!/bin/bash

set -e

# Wait for the database to be available
if [ -z "$SKIP_DATABASE_CHECK" ] || [ "$SKIP_DATABASE_CHECK" = "0" ]; then
  until nc -z -v -w30 "${DATABASE_HOST:-postgres}" "${DATABASE_PORT:-5432}"
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
    exec uwsgi --plugin http,python3 --master --http :8000 \
               --processes 4 --threads 1 \
               --need-app \
               --mount "${URL_PREFIX:-/}=smbackend/wsgi.py" \
               --manage-script-name \
               --die-on-term \
               --strict \
               --ignore-sigpipe \
               --ignore-write-errors \
               --disable-write-exception \
               --reload-on-rss 500
fi
