Service Map Backend
===================

This is the backend service for the Service Map UI.

Installation
------------

First, install the necessary Debian packages.

```python3-dev libyaml-dev libxml2-dev libxslt1-dev libpq-dev python-psycopg2 postgresql postgis postgresql-10-postgis-2.4``` 

You might need to start a new shell for the virtualenvwrapper commands to activate.

1. Make a Python virtual environment.

```virtualenv --python=python3 ven``` (mkvirtualenv -p /usr/bin/python3.4 smbackend)

2. Install pip requirements.

```pip install -r requirements.txt```
 
3. Setup the PostGIS database.

```
sudo su postgres
createuser -R -S -D -P smbackend
createdb -O smbackend -T template0 -l fi_FI.UTF8 -E utf8 smbackend
echo "CREATE EXTENSION postgis;" | psql smbackend
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

6. Import geo data.

```
./manage.py geo_import finland --municipalities
./manage.py geo_import helsinki --divisions
```
If problems with certificate, export certificate from complaining link and use this link as instruction https://superuser.com/questions/437330/how-do-you-add-a-certificate-authority-ca-to-ubuntu

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
