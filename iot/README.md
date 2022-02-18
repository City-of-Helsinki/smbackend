## About
The purpose of the IoT app is to store temporarly data from various IoT-data sources, that do not allow frequent fetching of their data.  
The data is stored as it is in JSON to a JSONField and served as JSON. The app uses caching to cache all its queries and serialized data. The Cache is cleared for the source when importing the data source or when a data source is added. The cache is populated if empty when serving data. 

## Adding IoT-data source from the Admin
* Give a tree letter long source name, this name will be the name for the source. Used for example when requesting the data.
* Add the full name of the source 
* Add the Url to the JSON data. 

## Setting periodic importing using Celery from the Admin
* Create a periodic task, give a descrpitive name.
* Select *iot.tasks.import_iot_data* as the Task (registered) 
* Choose the *Interval Schedule*
* Set the Start DateTime
* Add the source name as *Positional Arguments*, e.g. ["R24"] would import the source_name R24. 

## Manual import
To manually import source:
`./manage.py import_iot_data source_name`
Or by running the perioc task from the admin. 

## Retriving data
See: specification.swagger.yaml