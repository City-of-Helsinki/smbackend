import logging
from django.contrib.gis.geos import Point, Polygon
from django import db
from django.conf import settings
from .utils import (
    get_or_create_content_type,
    delete_mobile_units, 
    fetch_json, 
    GEOMETRY_URL
)
from mobility_data.models import (
    MobileUnit,
    ContentType,
    )
logger = logging.getLogger("mobility_data")
# The data comes from 2 different sources, the first contains basic info as position, address and type
CHARGING_STATIONS_URL1 = "https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/ChargingStations/FeatureServer/0/query?f=json&where=1=1&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=*"
# The second contains additional info as count , operator and power.
CHARGING_STATIONS_URL2 = "https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/ChargingStations/FeatureServer/1/query?f=json&where=1=1&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=*"


class ChargingStation:

    def __init__(self, elem, srid=settings.DEFAULT_SRID):
        self.is_active = True
        geometry = elem.get("geometry", None)
        attributes = elem.get("attributes", None)   
        self.object_id = attributes.get("OBJECTID", None)   
        x = geometry.get("x",0)
        y = geometry.get("y",0) 
        self.point = Point(x, y, srid=srid)
        self.name = attributes.get("NAME", "")
        self.address = attributes.get("ADDRESS", "")
        temp_str = self.address.split(",")[1].strip()        
        self.zip_code = temp_str.split(" ")[0]
        self.city = temp_str.split(" ")[1]
        self.url = attributes.get("URL", "")
        self.charger_type = attributes.get("TYPE", "")        
        self.url = attributes.get("URL", "")
        # address fields for service unit model
        self.street_address = self.address.split(",")[0]            
        self.address_postal_full = "{}{}".\
            format(self.address.split(",")[0], self.address.split(",")[1])
        # Initialize additional fields
        self.power = None
        self.operator = None
        self.count = None


    def set_additional_fields(self, elem):      
        self.power = elem.get("POWER", None)
        self.count = elem.get("COUNT", None)
        self.operator = elem.get("OPERATOR", None)
    

def get_filtered_charging_station_objects(json_data=None): 
    """
    Returns a list of ChargingStation objects that are filtered by location.
    """   
    geometry_data = fetch_json(GEOMETRY_URL) 
    # Polygon used the detect if point intersects. i.e. is in the boundries.
    polygon = Polygon(geometry_data["features"][0]["geometry"]["coordinates"][0])  
    if not json_data:
        json_data = fetch_json(CHARGING_STATIONS_URL1)
    srid = json_data["spatialReference"]["wkid"]
    objects = [ChargingStation(data, srid=srid) for data in json_data["features"]]
    filtered_objects = []
    # Filter objects
    for object in objects:    
        if polygon.intersects(object.point):
            filtered_objects.append(object)
    logger.info("Filtered: {} charging stations by location to: {}."\
        .format(len(json_data["features"]), len(filtered_objects)))        
    
    # Fetch the second url with the additionl data.
    json_data = fetch_json(CHARGING_STATIONS_URL2)
    # store all object_ids from filtered_object
    object_ids = [o.object_id for o in filtered_objects]
 
    # Iterate through the json_data and if object id matches with filtered object add
    #  additional fields  
    for elem in json_data["features"]:
        attributes = elem.get("attributes", None)
        object_id = attributes.get("OBJECTID")         
        if object_id in object_ids:
            # if object_id matches, set the additional fields. 
            # i.e. the charging_station is in the filtered_objects     
            for object in filtered_objects:
                if object.object_id == object_id:
                    object.set_additional_fields(attributes)
                    break          
                   
    return filtered_objects


@db.transaction.atomic    
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_mobile_units(ContentType.CHARGING_STATION)
    description = "Charging stations in province of SouthWest Finland."  
    name="Charging Station" 
    content_type, _ = get_or_create_content_type(
        ContentType.CHARGING_STATION, name, description)
    
    for object in objects:
        is_active = object.is_active 
        name = object.name
        address = object.address
        extra = {}
        extra["charger_type"] = object.charger_type
        extra["power"] = object.power
        extra["count"] = object.count 
        extra["operator"] = object.operator
        extra["url"] = object.url
        extra["mobile_unit"] = MobileUnit.objects.create(
            is_active=is_active,
            name=name,
            address=address,
            geometry=object.point,
            extra=extra,
            content_type=content_type
        )
    logger.info("Saved charging stations to database.")