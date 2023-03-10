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

Configure the data imports in the admin.
For detailed information about setting up the import tasks see:
https://github.com/City-of-Turku/smbackend/wiki/Celery-Tasks


## Manually Importing data
Note, All imports can and is recommended to be run from the Admin using Celery Tasks.

```
./manage.py geo_import finland --municipalities
./manage.py turku_services_import services accessibility units divisions addresses
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

Importing from external data sources should always be done after importing the services and units. External data sources are configured in:
smbackend_turku/importers/data/external_sources_config.yml

```
./manage.py turku_services_import external_sources
```
To delete all data imported from external sources:
```
./manage.py turku_services_import services units --delete-external-sources
```

To import a specific external data source give the name of the external data source
defined in the config file as argument.
e.g.:
```
./manage.py turku_services_import gas_filling_stations
```
Imports external data source named gas_filling_stations.

To delete a specific imported external data source:
e.g., remove external source named bicycle_stands.
```
./manage.py turku_services_import --delete-external-source bicycle_stands 
```
### Note
When importing services and units the ids are received from the source. Therefore the ids for the external sources must be manually set to avoid id collisions. 
The ids are configured in the smbackend_turku/importers/data/external_sources_config.yml
