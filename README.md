Service Map Backend
===================

This is the backend service for the Service Map UI.

Installation
------------

First, install the necessary Debian packages.

    libpython3.4-dev virtualenvwrapper libyaml-dev libxml2-dev libxslt1-dev

You might need to start a new shell for the virtualenvwrapper commands to activate.

1. Make a Python virtual environment.

`
mkvirtualenv -p /usr/bin/python3.4 smbackend
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
`

4. Modify `local_settings.py` to contain the local database info.

`
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': '127.0.0.1',
        'NAME': 'smbackend',
        'USER': 'smbackend',
        'PASSWORD': 'smbackend',
    }
}
`

5. Create database tables.

`
./manage.py syncdb
./manage.py migrate
`

6. Import geo data.

`
./manage.py geo_import finland --municipalities
./manage.py geo_import helsinki --divisions
`

