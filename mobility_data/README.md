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
./manage.py import_wfs PAZ
```

### Speed limit Zones
To import type:
```
./manage.py import_wfs SLZ
```

### Scooter Restriction
Imports parking(SPG), no parking(SNP) and speed limit zones(SSL).
To import data type:
```
./manage.py import_wfs SPG SSL SNP
```

### Accessories
Imports benches(ABH), public toilets(APT), tables(ATE) and furniture groups(AFG).
To import data type:
```
./manage.py import_wfs APT ATE ABH AFG
```
### Share car parking places
Imports parking places for car sharing cars. 
To import data type:
```
./manage.py import_share_car_parking_places
```

### Bicycle networks
Imports brush salted(BLB) and brush sanded bicycle networks(BND).
To import data type:
```
./manage.py import_wfs BLB BND
```

### Marinas
Imports marinas, guest marina and boat parking.
Imports also berths that belongs to marinas.
To import data type:
```
./manage.py import_marinas
```

### Disabled and no staff parkings
Imports disabled parkings and no staff parkings, i.e., no staff parking are parking places that are not intended for the staff.
To import data type:
```
./manage.py import_disabled_and_no_staff_parkings
```

### Loading and unloading places
To import data type:
```
./manage.py import_loading_and_unloading_places
```

### Lounaistieto shapefiles
The importer imports shapefiles from https://data.lounaistieto.fi and stores them
as mobility data. The importer can be configured by modifying the file:
/mobility_data/importers/data/lounaistieto_shapefiles_config.yml
Note, if a new data_source is added a content type must be added to the model.
To run the importer type:
```
./manage.py import_lounaistieto_shapefiles
```

### Paavonpolkus
To import data type:
```
./manage.py import_wfs PPU
```
### Paddling trails
To import data type:
```
./manage.py import_wfs PTL
```

### Hiking trails
To import data type:
```
./manage.py import_wfs NTL
```

### Nature trails
To import data type:
```
./manage.py import_wfs HTL
```

### Fitness trails
To import data type:
```
./manage.py import_wfs FTL
```

## Deletion
To delete mobile units for a content type.
```
./manage.py delete_mobility_data CONTENT_TYPE(S)
```
e.g., this would delete Paavonpolku mobile units,
```
./manage.py delete_mobility_data PPU
```
To get the list of content types and their full names type:
```
./manage.py delete_mobility_data -h
```
## WFS Importer
The WFS importer imports data from the open Turku WFS server.
To set up a data source for importing in the WFS importer, configure the data source in the mobility_data/importers/data/wfs_importer_config.yml file.
To import the data type:
```
./manage import_wfs CONTENT_TYPE
```