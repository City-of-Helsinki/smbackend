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
Before importing addresses make sure you have the turku_addresses.cvs file located in the projects data/ directory.  
```
./manage.py geo_import finland --municipalities
./manage.py turku_services_import services accessibility units addresses
```
After the first time data is imported run:
```
./manage.py index_search_column
```
This populates the search_columns that are used in full text search.
After this is rows are modified the search_column is updated using signals.

## Importing external data sources

Importing from external data sources should always be done after importing the services and units.
To delete all data imported from external sources:
```
manage.py turku_services_import services units --delete-external-sources
```

When importing services and units the ids are received from the source. Therefore the ids for the external sources must be manually set to avoid
id collisions. 
The ids are set in a dict in the .env file with following keys:
* service_node is the id of the service_node, recommended value < 3000000
* service is the id of the service, recommended value > 1000
* units_offset is the offset that will be given to the imported units ids, recommended value > 10000. 
Example:
GAS_FILLING_STATIONS_IDS=service_node=20000,service=20000,units_offset=20000

### Gas filling stations
Add following line to the .env file:
GAS_FILLING_STATIONS_IDS=service_node=20000,service=20000,units_offset=20000

To import type:
```
./manage.py turku_services_import gas_filling_stations
```

### Charging stations
Add following line to the .env file:
CHARGING_STATIONS_IDS=service_node=30000,service=30000,units_offset=30000

To import type:
```
./manage.py turku_services_import charging_stations
```
### Bicycle stands
Add following line to the .env file:
BICYCLE_STANDS_IDS=service_node=40000,service=40000,units_offset=40000

To import type:
```
./manage.py turku_services_import bicycle_stands
```