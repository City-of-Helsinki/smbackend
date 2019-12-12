#!/bin/bash

echo "Checking for database on host 'db', port 5432"
until nc -z -v -w30 "db" 5432
do
  echo "Waiting for postgres database connection..."
  sleep 1
done
echo "Database found!"

# Apply database migrations
echo "Applying database migrations"
python /code/manage.py migrate --noinput

set -e
# Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8000
