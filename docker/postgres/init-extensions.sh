#!/bin/sh
set -e

for ext in hstore pg_trgm; do
    create_ext_sql="CREATE EXTENSION IF NOT EXISTS $ext"
    echo "Installing $ext extension for template1"
    psql --username "$POSTGRES_USER" template1 -c "$create_ext_sql"
    echo "Installing $ext extension for $POSTGRES_DB database"
    psql --username "$POSTGRES_USER" "$POSTGRES_DB" -c "$create_ext_sql"
done
