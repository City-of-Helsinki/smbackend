
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

This will startup and bind local postgres, servicemap backend and servicemap frontend containers.

### Importing data

To import data for development usage and automatically index it, run command:
`docker-compose run servicemap maintenance_tasks all`

## Installation without Docker
------------

1. 
First, install the necessary Debian packages.

* libpython3.10-dev 
* python3.10-distutils
* virtualenvwrapper 
* libyaml-dev 
* libxml2-dev 
* libxslt1-dev
* voikko-fi
* libvoikko-dev

2. 
Clone the repository.
Use pyenv to manage python version and create a virtualenv with virtualenvwrapper.  
The virtualenv that will be created and used here is named "servicemap"
```
pyenv install -v 3.10.1
pyenv virtualenv 3.10.1 smbackend
pyenv local smbackend
pyenv virtualenvwrapper
mkvirtualenv servicemap
```

Installation and usage info for pyenv, pyenv-virtualenvwrapper and  
 virtualenvwrapper can be found here:
https://github.com/pyenv/pyenv-virtualenv
https://github.com/pyenv/pyenv-virtualenvwrapper
https://virtualenvwrapper.readthedocs.io/en/latest/install.html


3. Install pip requirements.
Be sure to load the virtualenv before installing the requirements:
Example with virtualenv named servicemap as created in example above.
```workon servicemap```
Install the requirements:
```pip install -r requirements.txt```

 If this error occurs:
```   
 ImportError: cannot import name 'html5lib' from 'pip._vendor' (/home/johndoe/.virtualenvs/servicemap/lib/python3.10/site-packages/pip/_vendor/__init__.py)
```
Try installing latest pip. 
```
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
```

4. Setup the PostGIS database.

Please note, we recommend PostgreSQL version 13 or higher.

Local setup:
First, ensure that the collation fi_FI.UTF-8 exists by entering the
postgresql shell with the psql command.
```
sudo su postgres
psql
SELECT * FROM pg_collation where collname like '%fi%';
```
There should be a collname fi_FI.UTF-8 if not you must create the collation.


```
sudo su postgres
psql
ALTER database template1 is_template=false;
DROP database template1;
CREATE DATABASE template1 WITH OWNER = postgres ENCODING = 'UTF8' TABLESPACE = pg_default LC_COLLATE = 'fi_FI.UTF-8' LC_CTYPE = 'fi_FI.UTF-8' CONNECTION LIMIT = -1 TEMPLATE template0;
ALTER database template1 is_template=true;
\q  
psql template1 -c 'CREATE EXTENSION IF NOT EXISTS postgis;'
psql template1 -c 'CREATE EXTENSION IF NOT EXISTS hstore;'
psql template1 -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;'
createuser -RSPd servicemap
createdb -O servicemap -T template1 -l fi_FI.UTF-8 -E utf8 servicemap
```

```
ERROR:  could not open extension control file "/usr/share/postgresql/14/extension/postgis.control": No such file or directory
```
Solution for ubuntu and Postgresql14:
```
sudo apt install postgis postgresql-14-postgis-3
```

Docker setup (modify as needed, starts the database on local port 8765):
```
docker run --name servicemap-psql -e POSTGRES_USER=servicemap -e POSTGRES_PASSWORD=servicemap -p 8765:5432 -d mdillon/postgis
# you'll need the hstore extension enabled:
echo "CREATE EXTENSION hstore;" | docker exec -i servicemap-psql psql -U servicemap
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

For Turku specific imports see smbackend_turku/README.md.
```
./manage.py geo_import finland --municipalities
./manage.py geo_import helsinki --divisions
./manage.py index_search_columns
```

7. Redis
Redis is used for caching and as a message broker for Celery.
Install Redis. Ubuntu: `sudo apt-get install redis-server`

8. Celery

Install and run a message broker such as Redis or RabbitMQ.
Redis is recommended as it is also used for caching.
Configure the message broker in the environment variable "CELERY_BROKER_URL".
Start a Celery worker to handle asynchronous tasks locally with command:
```
celery -A smbackend worker -l INFO
```
Note, in production environment the celery worker can be run as a daemon.
https://docs.celeryproject.org/en/stable/userguide/daemonizing.html#daemonizing
Start Celery beat to handle scheduled periodic tasks with command:
```
celery -A smbackend beat -l INFO
```

Observations
------------
Not used in the Turku servicemap.

Load the initial observation data with the command:
```
./scripts/import_observation_initial_data.sh
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

The error:
 ```
  psycopg2.errors.UndefinedObject: operator class "gin_trgm_ops" does not exist for access method "gin"
```
Can be fixed by adding the pg_trgm extension to the database:
```
psql template1 -c 'CREATE EXTENSION IF NOT EXISTS pg_trgm;'
```