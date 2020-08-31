# Smbackend Turku

Django app for importing Turku specific data to the service.

## Installation

Add following settings to config_dev.env:

```
ADDITIONAL_INSTALLED_APPS=smbackend_turku
TURKU_API_KEY=secret
ACCESSIBILITY_SYSTEM_ID=secret
```

## Importing data
```
./manage.py geo_import finland --municipalities
./manage.py turku_services_import services accessibility units addresses
./manage.py rebuild_index
```
