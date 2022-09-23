# Street Maintance

Django app for importings and serving street maintance data.

## Importer
To import data run:
```
./manage.py import_street_maintance_history
```
To periodically import data use Celery, for more information [see](https://github.com/City-of-Turku/smbackend/wiki/Celery-Tasks#street-maintenance-history-street_maintenancetasksimport_street_maintenance_history).

### History size
The default history size for a maintance unit is 10000. To import with a different history size:
```
./manage.py import_street_maintenance_history --history-size SIZE
```

## API
See: specificatin.swagger.yaml