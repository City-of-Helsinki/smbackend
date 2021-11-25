# Bicycle Network App
This app filters and stores uploaded bicycle networks. 

## Uploading files
The uploading is done through the django admin by editing the BicycleNetworkSource object.  
This objects can not be delete or new  instances can not be made.   
There are 3 different networks that can be uploaded
1. main network
2. local network
3. quality lanes

After uploading the file is filtered, i.e. properties that are not used are thrown away.   
The data is stored to the database and also 
a filtered geojson version is stored under MEDIA_ROOT/bicycle_network/ filtered/.  
Names of the filtered files are the same as the networks,  i.e. "main_network",    
"local_network" and "quality_lanes".  
By default the geometry data is transformed to srid 4326.  
Finally the uploaded files containing the network data are deleted,   thus they are obsolete.  

## Consuming the data
The data can be consumed from the endpoints, see: specification.swagger.2.0.yaml for more details.  
The filtered .geojson files can be found under  
MEDIA_ROOT/bicycle_network/filtered/ , Note this needs to be configured   
in the production webserver. The directory is only visible when django  is run in debug mode.