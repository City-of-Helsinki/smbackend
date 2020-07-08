[![Build status](https://api.travis-ci.com/City-of-Helsinki/smbackend.svg?branch=master)](https://travis-ci.org/github/City-of-Helsinki/smbackend)
[![Codecov](https://codecov.io/gh/City-of-Helsinki/smbackend/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/smbackend)
[![Requirements](https://requires.io/github/City-of-Helsinki/smbackend/requirements.svg?branch=master)](https://requires.io/github/City-of-Helsinki/smbackend/requirements/?branch=master)

Service Map Backend
===================

This is the backend service for the Service Map UI.

Installation with Docker Compose
------------

First configure development environment settings as stated in `config_dev.env.example` and in `config_dev_ui.env.example`.

### Running the application

Run application with `docker-compose up`

This will startup and bind local postgres, elasticsearch, servicemap backend and servicemap frontend containers.

### Importing data

To import data for development usage and automatically index it, run command:
`docker-compose run servicemap maintenance_tasks all`

Installation without Docker
------------

First, install the necessary Debian packages.

    libpython3.7-dev virtualenvwrapper libyaml-dev libxml2-dev libxslt1-dev

You might need to start a new shell for the virtualenvwrapper commands to activate.

1. Make a Python virtual environment.

```
mkvirtualenv -p /usr/bin/python3 servicemap
```

2. Install pip requirements.

    ```pip install -r requirements.txt```
 
3. Setup the PostGIS database.

Please note we require PostgreSQL version 9.4 or higher

Local setup:

```
sudo su postgres

psql template1 -c 'CREATE EXTENSION IF NOT EXISTS postgis;'
psql template1 -c 'CREATE EXTENSION IF NOT EXISTS hstore;'

createuser -RSPd servicemap

createdb -O servicemap -T template1 -l fi_FI.UTF-8 -E utf8 servicemap

```

Docker setup (modify as needed, starts the database on local port 8765):
```
docker run --name servicemap-psql -e POSTGRES_USER=servicemap -e POSTGRES_PASSWORD=servicemap -p 8765:5432 -d mdillon/postgis
# you'll need the hstore extension enabled:
echo "CREATE EXTENSION hstore;" | docker exec -i servicemap-psql psql -U servicemap
```

4. Modify `local_settings.py` to contain the local database info.

```
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': '127.0.0.1',
        'NAME': 'servicemap',
        'USER': 'servicemap',
        'PASSWORD': 'servicemap',
    }
}
```

5. Create database tables.

```
./manage.py migrate
```

If this command fails with: `django.core.exceptions.ImproperlyConfigured: GEOS is required and has not been detected.`,
then install the GEOS library. On a Mac this can be achieved with HomeBrew:
```
brew install geos
```

6. Import geo data.

```
./manage.py geo_import finland --municipalities
./manage.py geo_import helsinki --divisions
```

Search
------

You can configure multilingual Elasticsearch-based search by including
something like the following in your `local_settings.py`:

```python
import json
def read_config(name):
    return json.load(open(
        os.path.join(
            BASE_DIR,
            'smbackend',
            'elasticsearch/{}.json'.format(name))))

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'multilingual_haystack.backends.MultilingualSearchEngine',
    },
    'default-fi': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-fi',
        'MAPPINGS': read_config('mappings_finnish')['modelresult']['properties'],
        'SETTINGS': read_config('settings_finnish')
    },
    'default-sv': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-sv',
        'MAPPINGS': read_config('mappings_swedish')['modelresult']['properties'],
        'SETTINGS': read_config('settings_swedish')
    },
    'default-en': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-en',
        'MAPPINGS': read_config('mappings_english')['modelresult']['properties'],
        'SETTINGS': read_config('settings_english')
    },
}
```


Troubleshooting
---------------

The error:
```
OSError: dlopen(/usr/local/lib/libgdal.dylib, 6): Symbol not found: _GEOSArea
```
Can be fixed by adding this to local_settings.py:
```python
GDAL_LIBRARY_PATH = "/usr/local/lib/libgdal.dylib"
import ctypes
ctypes.CDLL(GDAL_LIBRARY_PATH)
```
