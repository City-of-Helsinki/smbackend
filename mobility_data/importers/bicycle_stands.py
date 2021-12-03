import logging
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
from django.contrib.gis.geos import Point
from django import db
from .utils import (
    get_municipality_name, 
    get_closest_street_name,
    delete_mobile_units,
    get_or_create_content_type,
    get_street_name_translations,
    set_translated_field,
)   
from mobility_data.models import (
    MobileUnit, 
    ContentType, 
)
BICYCLE_STANDS_URL = "http://tkuikp/TeklaOGCWeb/WFS.ashx?service=WFS&request=GetFeature&typeName=GIS:Polkupyoraparkki&outputFormat=GML3"
SOURCE_DATA_SRID = 3877
logger = logging.getLogger("mobility_data")

class BicyleStand:
    HULL_LOCKABLE_MAPPINGS = {
        "Runkolukitusmahdollisuus": True,
        "Ei runkolukitusmahdollisuutta" : False,
        "Katettu, runkolukitusmahdollisuus": True,
        "Katettu, ei runkolukitusmahdollisuutta": False
    }
    COVERED_IN_STR = "Katettu"
    model = None
    name = None
    number_of_stands = None
    number_of_places = None # The total number of places for bicycles.     
    hull_lockable = None
    covered = None
    point = None
    city = None
    street_address = None
    
    def __init__(self, bicycle_stand, namespaces):
        self.name = {}
        self.street_address = {}
        
        geometry = bicycle_stand.find(f"{{{namespaces['GIS']}}}Geometry")
        point = geometry.find(f"{{{namespaces['gml']}}}Point")
        pos = point.find(f"{{{namespaces['gml']}}}pos").text.split(" ")
        self.point = Point(float(pos[0]), float(pos[1]), srid=SOURCE_DATA_SRID)
      
        model_elem = bicycle_stand.find(f"{{{namespaces['GIS']}}}Malli")
        if model_elem != None:
            self.model = model_elem.text
        katu_name_elem = bicycle_stand.find(f"{{{namespaces['GIS']}}}Katuosa_nimi")
        viher_name_elem = bicycle_stand.find(f"{{{namespaces['GIS']}}}Viherosa_nimi")

        if katu_name_elem != None:
            name = katu_name_elem.text
        elif viher_name_elem != None:
            name = viher_name_elem.text
        else:
            name = get_closest_street_name(self.point)

        num_stands_elem = bicycle_stand\
            .find(f"{{{namespaces['GIS']}}}Lukumaara")
  
        if num_stands_elem != None:
            self.number_of_stands = int(num_stands_elem.text)
        
        num_places_elem = bicycle_stand\
            .find(f"{{{namespaces['GIS']}}}Pyorapaikkojen_lukumaara")
       
        if num_places_elem != None:
            # Parse the numbers inside the string and finally sum them.
            # The input can contain string such as "8 runkolukittavaa ja 10 ei runkolukittavaa paikkaa"
            numbers = [int(s) for s in num_places_elem.text.split() if s.isdigit()]
            self.number_of_places = sum(numbers)
       
        quality_elem  = bicycle_stand\
            .find(f"{{{namespaces['GIS']}}}Pyorapaikkojen_laatutaso")

        if quality_elem != None: 
            quality_text = quality_elem.text
            self.hull_lockable = self.HULL_LOCKABLE_MAPPINGS[quality_text]        
            if self.COVERED_IN_STR in quality_text:
                self.covered = True
            else:
                self.covered = False
            
        translated_names = get_street_name_translations(name)
        self.name["fi"] = translated_names["fi"]
        self.name["sv"] = translated_names["sv"]
        self.name["en"] = translated_names["fi"]
  
        self.city = get_municipality_name(self.point)


def get_bicycle_stand_objects(json_data=None):
    namespaces = {"gml":"http://www.opengis.net/gml", "GIS":"http://www.tekla.com/schemas/GIS"}

    response = requests.get(BICYCLE_STANDS_URL)
    assert response.status_code == 200, "Fetching {} status code: {}".\
        format(BICYCLE_STANDS_URL, response.status_code)
    gml = ET.fromstring(response.content)
    find_str = f"{{{namespaces['gml']}}}featureMember"
    feature_members = gml.findall(find_str)
    bicycle_stands = []
    for feature_member in feature_members:
        bicycle_stand = feature_member.find(f"{{{namespaces['GIS']}}}Polkupyoraparkki")
        #id = bicycle_stand.find(f"{{{namespaces['GIS']}}}Id").text
        # if id == "0":            
        #     continue
        bicycle_stands.append(BicyleStand(bicycle_stand, namespaces))
    return bicycle_stands

@db.transaction.atomic 
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_mobile_units(ContentType.BICYCLE_STAND)        
    description = "Bicycle stands in The Turku Region."
    name = "Bicycle Stands"
    content_type, _ = get_or_create_content_type(
        ContentType.BICYCLE_STAND, name, description
    )
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type,             
        )
        extra = {}
        extra["model"] = object.model
        extra["number_of_stands"] = object.number_of_stands
        extra["number_of_places"] = object.number_of_places
        extra["hull_lockable"] = object.hull_lockable
        extra["covered"] = object.covered
        mobile_unit.extra = extra

        set_translated_field(mobile_unit, "name", object.name)
        mobile_unit.save()