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

## Importing external data sources

Importing from external data sources should always be done after importing the services and units.

### Gas filling stations
```
./manage.py turku_services_import gas_filling_stations
```

### Charging stations
```
./manage.py turku_services_import charging_stations
```
