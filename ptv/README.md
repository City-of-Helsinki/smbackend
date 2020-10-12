# PTV

Django app for importing data from PTV (Suomi.fi-palvelutietovaranto) to the services API.

The app is compatible with `smbackend_turku` and currently uses service nodes imported from it.

## Installation

Add following settings to config_dev.env:

```
ADDITIONAL_INSTALLED_APPS=ptv,smbackend_turku
```

## Importing data
```
./manage.py geo_import finland --municipalities
./manage.py turku_services_import services
./manage.py ptv_import <municipality code(s)>
./manage.py rebuild_index
```
