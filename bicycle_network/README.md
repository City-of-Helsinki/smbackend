# Bicycle Network App
This app filters and stores uploaded bicycle networks. 

## Uploading files
The uploading is done through the django admin by adding/eidting a BicycleNetwork
instance by adding the geojson file that contains the route.

After uploading the file is filtered and all properties are thrown away.   
If possible overlapping linestrings are merged. If this it not possible a warning
message is displayed. This causes no harm.
By default the geometry data is transformed to srid 4326.  
Finally the uploaded files containing the network data are deleted,   thus they are obsolete.  

## Consuming the data
The data can be consumed from the endpoints, see: specification.swagger.2.0.yaml for more details.  
