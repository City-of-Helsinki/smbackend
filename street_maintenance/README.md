# Street Maintance history

Django app for importing and serving street maintenance data.

## Importer
Name:
import_street_maintenance_history 

Providers:
* YIT
* KUNTEC
* INFRAROAD
* DESTIA

Parameters:
* --providers, list of providers to import, e.g., --provider yit kuntec 
* --history-size, the number of days to import (default is 4 and max is 31)
* --fetch-size (only available for infraroad and destia), the number of works to import per unit(default is 10000).

### Examples:
To import DESTIA street maintenance history with history size 2:
```
./manage.py import_street_maintenance_history --providers destia --history-size 2
```
To import KUNTEC and INFRAROAD street maintenance history:
```
./manage.py import_street_maintenance_history --providers kuntec infraroad
```
Note, only the MaintenanceWorks and MaintenanceUnits for the given provider from the latest import are stored and the rest are deleted. The GeometryHistory is generated only if more than one MaintenanceWork is created.

### Periodically imorting
To periodically import data use Celery, for more information [see](https://github.com/City-of-Turku/smbackend/wiki/Celery-Tasks#street-maintenance-history-street_maintenancetasksimport_street_maintenance_history).


## Deleting street maintenance history for a provider
It is possible to delete street maintenance history for a provider.
e.g., to delete all street maintenance history for provider 'destia':
```
./manage.py delete_street_maintenance_history destia
```

## API
See: specificatin.swagger.yaml