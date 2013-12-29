Service Map Backend
===================

This is the backend service for the Service Map UI.

Installation
------------

First, install the necessary Debian packages.

    libpython3.3-dev

1. Make a Python virtual environment.

`
mkvirtualenv smbackend
`

2. Install pip requirements.

`
pip install -r requirements.txt
`

3. Setup the PostGIS database.

`
sudo su postgres
createuser -R -S -D -P smbackend
createdb -O smbackend -T template0 -l fi_FI.UTF8 -E utf8 smbackend
echo "CREATE EXTENSION postgis;" | psql smbackend
echo "CREATE EXTENSION postgis_topology;" | psql smbackend
`
