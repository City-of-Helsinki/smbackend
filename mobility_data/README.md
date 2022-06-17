# MobilityData

Django app for importing and serving data from external sources.  
Add the TURKU_WFS_URL for the WFS server to the env, e.g.
```
TURKU_WFS_URL=https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx
```

## importers
It is recommended to use Celery tasks to import the mobility data,
see: https://github.com/City-of-Turku/smbackend/wiki/Celery-Tasks

To import all data sources:
```
./manage.py import_mobility_data
```
The data sources can be imported separetely as explained below:

### Gas filling stations  
To import data type:  
```
./manage.py import_gas_filling_stations  
```
### Charging stations  
To import data type:  
```
./manage.py import_charging_stations  
```
### Culture Routes
To import data type:  
```
./manage.py import_culture_routes  
```
Culture routes are not deleted before importing. To explicity delete Culture Routes before importing type:  
```
./manage.py import_culture_routes --delete  
```
### Bicycle stands  
To import data type:  
```
./manage.py import_bicycle_stands 
```

### Bike service stations
To import data type:  
```
./manage.py import_bike_service_stations
```

### Payment Zones
To import data type:
```
./manage.py import_payment_zones
```

### Speed limit Zones
To import type:
```
./manage.py import_speed_limit_zones
```

### Scooter Restriction
Imports parking, no parking and speed limit zones.
To import data type:
```
./manage.py import_scooter_restrictions
```

### Accessories
Imports benches, public toilets, tables and furniture groups.
To import data type:
```
./manage.py import_accessories
```
### Share car parking places
Imports parking places for car sharing cars. 
To import data type:
```
./manage.py import_share_car_parking_places
```

### Bicycle networks
Imports brush salted and brush sanded bicycle networks.
To import data type:
```
./manage.py import_bicycle_networks
```

### Marinas
Imports marinas, guest marina and boat parking.
To import data type:
```
./manage.py import_marinas
```