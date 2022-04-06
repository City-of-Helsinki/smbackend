# Smbackend Turku

Django app for importing Turku specific data to the service.

## Installation

Add following settings to config_dev.env:

```
ADDITIONAL_INSTALLED_APPS=smbackend_turku
TURKU_API_KEY=secret
ACCESSIBILITY_SYSTEM_ID=secret
```
And the Mobile view specific settings, see: config_dev.env.example

## Manually Importing data
Note, All imports can be run from the Admin using Celery Tasks.

```
./manage.py geo_import finland --municipalities
./manage.py turku_services_import services accessibility units addresses
```

## Enricing addresses with geo-search-data
This enriches addresses imported with the address importer(from the WFS server)
```
./manage.py turku_services_import enriched_addresses
```

## Importing addresses from geo-search
```
./manage.py turku_services_import geo_search_addresses
```
Note, this imports all the addresses from Southwest Finland and might take ~9 hours.

##  Indexing search columns
The search columns must be indexed after the first time data is imported or geo-search addesses are imported or addesses are enriched with geo-search data.
```
./manage.py index_search_column
```
This populates the search_columns that are used in full text search.
After this is rows are modified the search_column is updated using signals.
Note, if geo-search addresses are imported this might take ~45minutes.

## Importing external data sources

Importing from external data sources should always be done after importing the services and units.
To import the mobility data, currently imports: charging stations, gas filling stations and bicycle stands.
```
./manage.py turku_services_import mobility_data
```
To delete all data imported from external sources:
```
./manage.py turku_services_import services units --delete-external-sources
```
Currently following importers import to the mobility view by setting
a id, which is used to retrieve the data from the service_unit table:
gas_filling_stations, charging_stations and bicycle_stands. e.g. These
importers import data to both the services list and mobility view.

When importing services and units the ids are received from the source. Therefore the ids for the external sources must be manually set to avoid id collisions. 
The ids are set in a dict in the .env file with following keys:
* service_node is the id of the service_node, recommended value < 3000000
* service is the id of the service, recommended value > 1000
* units_offset is the offset that will be given to the imported units ids, recommended value > 10000. 
Example:
GAS_FILLING_STATIONS_IDS=service_node=200000,service=200000,units_offset=200000

### Gas filling stations
Add following line to the .env file:
GAS_FILLING_STATIONS_IDS=service_node=200000,service=200000,units_offset=200000

To import type:
```
./manage.py turku_services_import gas_filling_stations
```

### Charging stations
Add following line to the .env file:
CHARGING_STATIONS_IDS=service_node=300000,service=300000,units_offset=300000

To import type:
```
./manage.py turku_services_import charging_stations
```
### Bicycle stands
Add following line to the .env file:
BICYCLE_STANDS_IDS=service_node=400000,service=400000,units_offset=400000

To import type:
```
./manage.py turku_services_import bicycle_stands
```