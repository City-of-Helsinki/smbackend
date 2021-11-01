import logging
from django.contrib.gis.geos import GEOSGeometry, Point, Polygon
from django import db
from django.conf import settings
from mobility_data.models import (
    MobileUnit, 
    ContentType, 
    GasFillingStationContent
)
from .utils import fetch_json, delete_tables, GEOMETRY_URL
logger = logging.getLogger("__name__")
GAS_FILLING_STATIONS_URL = "https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/GasFillingStations/FeatureServer/0/query?f=json&where=1%3D1&outFields=OPERATOR%2CLAT%2CLON%2CSTATION_NAME%2CADDRESS%2CCITY%2CZIP_CODE%2CLNG_CNG%2CObjectId"


class GasFillingStation:

    def __init__(self, elem, srid=settings.DEFAULT_SRID):
        self.is_active = True
        attributes = elem.get("attributes")        
        x = attributes.get("LON",0)
        y = attributes.get("LAT",0)
        self.point = Point(x, y, srid=srid)              
        self.name = attributes.get("STATION_NAME", "")
        self.address = attributes.get("ADDRESS", "")        
        self.zip_code = attributes.get("ZIP_CODE", "")
        self.city = attributes.get("CITY", "")      
        self.operator = attributes.get("OPERATOR", "")
        self.lng_cng = attributes.get("LNG_CNG", "") 
        # address fields for service unit model
        self.street_address = self.address.split(",")[0]        
        self.address_postal_full = "{} {} {}"\
            .format(self.address, self.zip_code, self.city)

def get_filtered_gas_filling_station_objects(json_data=None): 
    """
    Returns a list of GasFillingStation objects that are filtered by location.
    """   
    geometry_data = fetch_json(GEOMETRY_URL) 
    # Polygon used the detect if point intersects. i.e. is in the boundries.
    polygon = Polygon(geometry_data["features"][0]["geometry"]["coordinates"][0])  
    if not json_data:
        json_data = fetch_json(GAS_FILLING_STATIONS_URL)
    #srid = json_data["spatialReference"]["wkid"]
    # NOTE, hack to fix srid 102100 causes "crs not found"
    srid = 4326
    # Create list of GasFillingStation objects
    objects = [GasFillingStation(data, srid=srid) for data in json_data["features"]]
    filtered_objects = []
    # Filter objects by their location
    for object in objects:
        if polygon.intersects(object.point):
            filtered_objects.append(object)
    logger.info("Filtered: {} gas filling stations by location to: {}."\
        .format(len(json_data["features"]), len(filtered_objects)))        
    return filtered_objects

@db.transaction.atomic  
def save_to_database(objects, delete_table=True):
    if delete_table:
        delete_tables(ContentType.GAS_FILLING_STATION)        
    description = "Gas filling stations in province of SouthWest Finland."
    content_type, _ = ContentType.objects.get_or_create(
        type_name=ContentType.GAS_FILLING_STATION,
        name="Gas Filling Station",
        class_name=ContentType.CONTENT_TYPES[ContentType.GAS_FILLING_STATION],
        description=description
    )
    for object in objects:
        is_active = object.is_active    
        name = object.name
        address = object.address       
        address += ", " + object.zip_code + " " + object.city
        operator = object.operator
        lng_cng = object.lng_cng 
        mobile_unit = MobileUnit.objects.create(
            is_active=is_active,
            name=name,
            address=address,
            geometry=object.point,
            content_type=content_type
        )
        content = GasFillingStationContent.objects.create(
            mobile_unit=mobile_unit,
            operator=operator,
            lng_cng=lng_cng
        )        

    logger.info("Saved gas filling stations to database.")
