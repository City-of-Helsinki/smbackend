# Street Maintance

Django app for importing and serving street maintenance data.

## Importers

### Infraroad
```
./manage.py import_infraroad_street_maintenance_history
```
### YIT
```
./manage.py import_yit_street_maintenance_history
```
### Kuntec
```
./manage.py import_kuntec_street_maintenance_history
```

### Destia
```
./manage.py import_destia_street_maintenance_history
```

### Periodically imorting
To periodically import data use Celery, for more information [see](https://github.com/City-of-Turku/smbackend/wiki/Celery-Tasks#street-maintenance-history-street_maintenancetasksimport_street_maintenance_history).

## History sizes
To set the history size use the '--history-size' parameter and give the value as argument.
e.g., would import the Autori data for the last 30 days.
```
./manage.py import_yit_street_maintenance_history --history-size 30
```
### Infraroad
The default history size for a infraroad maintenance unit is 10000. That is works per unit. A work contains the timestamp, point data and events.
### Destia
The default history size for a Destia maintenance unit is 10000. 
### Yit
The history size is in days. The default is 5.
Note, the max size for Autori history is 31 days.
### Kuntec
The history size is in days. The default is 5.
Note, the max size for Kuntec history is 31 days.
## API
See: specificatin.swagger.yaml