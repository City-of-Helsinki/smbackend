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
./manage.py import_wfs PaymentZone
```

### Speed limit Zones
To import type:
```
./manage.py import_wfs SpeedLimitZone
```

### Scooter Restriction
To import data type:
```
./manage.py import_wfs ScooterParkingArea ScooterSpeedLimitArea ScooterNoParkingArea
```

### Accessories
Imports public benches, toilets, tables and furniture groups.
To import data type:
```
./manage.py import_wfs PublicToilet PublicTable PublicBench PublicFurnitureGroup
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
./manage.py import_wfs BrushSaltedBicycleNetwork BrushSandedBicycleNetwork
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
./manage.py import_wfs PaavonPolku
```
### Paddling trails
To import data type:
```
./manage.py import_wfs PaddlingTrail
```

### Hiking trails
To import data type:
```
./manage.py import_wfs HikingTrail
```

### Nature trails
To import data type:
```
./manage.py import_wfs NatureTrail
```

### Fitness trails
To import data type:
```
./manage.py import_wfs FitnessTrail
```

### Crosswalk signs
```
./manage.py import_wfs CrossWalkSign

```
### Disabled parking signs
```
./manage.py import_wfs DisabledParkingSign
```

### Föli stops
```
./manage.py import_foli_stops
```

### Barbecue places
```
./manage.py import_wfs BarbecuePlace
```


### Playgrounds
```
./manage.py import_wfs PlayGround
```

### Föli park and ride stop
Imports park and ride stops for bikes and cars.
```
./manage.py import_foli_parkandride_stops
```

### Outdoor gym devices
Imports the outdoor gym devices from the services.unit model. i.e., sets references by id to the services.unit model. The data is then serialized from the services.unit model.
```
./manage.py import_outdoor_gym_devices
```

### Parking machines
```
./manage.py import_parking_machines
```

## Deletion
To delete mobile units for a content type.
```
./manage.py delete_mobility_data CONTENT_TYPE_NAMES(S)
```
e.g., this would delete Paavonpolku mobile units,
```
./manage.py delete_mobility_data PaavonPolku
```

## WFS Importer
The WFS importer imports data from the open Turku WFS server.
To set up a data source for importing in the WFS importer, configure the data source in the mobility_data/importers/data/wfs_importer_config.yml file.
To import the data type:
```
./manage import_wfs CONTENT_TYPE_NAME
```

For configuration example and documentation see: 
mobility_data/importers/data/wfs_importer_config_example.yml