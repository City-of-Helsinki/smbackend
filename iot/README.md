## About
The purpose of the iot app is to store temporarly data from various IoT source.
The data is stored as it is in JSON to a JSONField. 


Data is retrieved, cache i
blahblah ... FIX this.
celery task.

## Adding IoT-data source
* Give a tree letter long name, this name will be the name for the source. Used
for example when quering.
* Add the full name of the source that explain and the Url to the JSON data. 


## Manual import

`./manage.py import_iot_data source_name`


## Periodic importing using Celery
* Create a periodic task, select iot.tasks.import_iot_data as the Task (registered) 
* Choose the Interval Schedule
* Set the Start DateTime
* Add the source name as positional argument, e.g. ["R24"] would import the
source_name R24. 


## Retriving data
See: specification.swagger.yaml