Service Map Backend
===================

This is the backend service for the Service Map UI.

Installation
------------

First, install the necessary Debian packages.

```
python3-dev libyaml-dev libxml2-dev libxslt1-dev libpq-dev python-psycopg2 postgresql postgis postgresql-10-postgis-2.4
``` 

You might need to start a new shell for the virtualenvwrapper commands to activate.

1. Make a Python virtual environment.

```
virtualenv --python=python3 venv
source venv/bin/activate
```

2. Install pip requirements.

```pip install -r requirements.txt```
 
3. Setup the PostGIS database.

```
sudo su postgres
createuser -R -S -D -P smbackend
createdb -O smbackend -T template0 -l fi_FI.UTF8 -E utf8 smbackend
echo "CREATE EXTENSION postgis;" | psql smbackend
echo "CREATE EXTENSION hstore;" | psql smbackend
psql -d smbackend -c 'ALTER USER smbackend with createdb;'
psql -d smbackend -c 'ALTER ROLE smbackend SUPERUSER;'
psql -d template1 -c 'create extension hstore;'

```


Docker setup (modify as needed, starts the database on local port 8765):
```
docker run --name smbackend-psql -e POSTGRES_USER=smbackend -e POSTGRES_PASSWORD=smbackend -p 8765:5432 -d mdillon/postgis
# you'll need the hstore extension enabled:
echo "CREATE EXTENSION hstore;" | docker exec -i smbackend-psql psql -U smbackend
```


4. Create `local_settings.py` to contain the local database info.

```
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': '127.0.0.1',
        'NAME': 'smbackend',
        'USER': 'smbackend',
        'PASSWORD': 'smbackend',
    }
}
```

5. Create database tables.

```./manage.py migrate```

If this command fail with: `django.core.exceptions.ImproperlyConfigured: GEOS is required and has not been detected.`,
then install the GEOS library. On a Mac this can be achieved with HomeBrew:
```
brew install geos

6. Import geo data.

```
./manage.py geo_import finland --municipalities
./manage.py geo_import helsinki --divisions
```
If problems with certificate occurs, export certificate from erroring link and use this instructions: https://superuser.com/questions/437330/how-do-you-add-a-certificate-authority-ca-to-ubuntu

Update map with

```scripts/update.sh```

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
    },
    'default-en': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-en',
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
