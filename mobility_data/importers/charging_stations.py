import logging
from django.contrib.gis.geos import Point, Polygon
from django import db
from django.conf import settings
from .utils import (
    get_or_create_content_type,
    delete_mobile_units, 
    get_street_name_translations,
    fetch_json, 
    set_translated_field,
    get_street_name_and_number,
    GEOMETRY_URL,
    LANGUAGES
)
from mobility_data.models import (
    MobileUnit,
    ContentType,
    mobile_unit,
    )
logger = logging.getLogger("mobility_data")
# The data comes from 2 different sources, the first contains basic info as position, address and type
CHARGING_STATIONS_URL1 = "https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/ChargingStations/FeatureServer/0/query?f=json&where=1=1&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=*"
# The second contains info about the chargers as count , operator and power.
CHARGING_STATIONS_URL2 = "https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/ChargingStations/FeatureServer/1/query?f=json&where=1=1&returnGeometry=true&spatialRel=esriSpatialRelIntersects&outFields=*"


class ChargingStation:
    
    
    def __init__(self, elem, srid=settings.DEFAULT_SRID):
        self.is_active = True
        self.address = {}
        #Contains Only steet_name and number
        self.street_address = {}
        geometry = elem.get("geometry", None)
        attributes = elem.get("attributes", None) 
        # Location id is used as reference to chargers in second data source.  
        self.location_id = attributes.get("LOCATION_ID", None)   
        x = geometry.get("x",0)
        y = geometry.get("y",0) 
        self.point = Point(x, y, srid=srid)
        self.name = attributes.get("NAME", "")
        address_field = attributes.get("ADDRESS", "").lstrip().split(",")
        street_name, street_number = get_street_name_and_number(address_field[0])
        # if len is >1 address contains zip and city
        if (len(address_field)>1):
            zip_and_city = address_field[1].lstrip().split(" ")            
            if (len(zip_and_city)>0 and zip_and_city[0].isdigit()):
                self.zip_code = zip_and_city[0]
            else:
                self.zip_code = ""
            if (len(zip_and_city)>1):
                self.city = zip_and_city[1]
            else:
                self.city = ""
               
        self.url = attributes.get("URL", "")
        translated_street_names = get_street_name_translations(
            street_name)               
        for lang in LANGUAGES:            
            if street_number:
                self.address[lang] = f"{translated_street_names[lang]} {street_number}, " 
                self.address[lang] += f"{self.zip_code} {self.city}"
                self.street_address[lang] = f"{translated_street_names[lang]} {street_number}"
            else:
                self.address[lang] = f"{translated_street_names[lang]}, {self.zip_code} {self.city}"
                self.street_address[lang] = f"{translated_street_names[lang]}"
                 
        self.chargers = []      

    
    def add_charger(self, elem):
        charger = {}
        charger["type"] = elem.get("TYPE", None)
        charger["power"] = elem.get("POWER", None)
        charger["count"] = elem.get("COUNT", None)
        charger["operator"] = elem.get("OPERATOR", None)
        self.chargers.append(charger)
        

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
    # store all location_ids from filtered_object
    location_ids = [o.location_id for o in filtered_objects]
    # Iterate through the json_data and if location id matches with filtered object 
    # add charger.
    for elem in json_data["features"]:
        attributes = elem.get("attributes", None)
        location_id = attributes.get("LOCATION_ID", 0)    
        if location_id in location_ids:
            # if location_id matches, add the charger 
            # i.e. the charging_station is in the filtered_objects     
            for object in filtered_objects:
                if object.location_id == location_id:
                    object.add_charger(attributes)
                    #break             
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
        extra = {}       
        extra["url"] = object.url
        extra["chargers"] = object.chargers
        mobile_unit = MobileUnit.objects.create(
            is_active=is_active,
            name=name,
            geometry=object.point,
            extra=extra,
            content_type=content_type
        )
        set_translated_field(mobile_unit, "address", object.address)  
        mobile_unit.save()
  
    logger.info("Saved charging stations to database.")