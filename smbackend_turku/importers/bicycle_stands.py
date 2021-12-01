from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from requests.api import get
from services.models import (
    Service,
    ServiceNode,
    Unit,   
    UnitServiceDetails,
    
)
from munigeo.models import Address, Street
from services.management.commands.services_import.services import (
    update_service_node_counts,  
)
from smbackend_turku.importers.stations import create_language_dict   
from smbackend_turku.importers.utils import (   
    set_field,
    set_tku_translated_field,
    create_service,
    create_service_node,
    get_municipality,
    get_municipality_name,
    UTC_TIMEZONE,
)

URL = "http://tkuikp/TeklaOGCWeb/WFS.ashx?service=WFS&request=GetFeature&typeName=GIS:Polkupyoraparkki&outputFormat=GML3"
#, 1= katettu ja runkolukittava, 2=runkolukittava, 3=ei runkolukitusmahdollisuutta (vaikka olisi katettu). 
SOURCE_DATA_SRID = 3877

class BicyleStand:
    HULL_LOCKABLE_MAPPINGS = {
        "Runkolukitusmahdollisuus": True,
        "Ei runkolukitusmahdollisuutta" : False
    }
    model = None
    name = None
    number_of_stands = None
    number_of_places = None # The total number of places for bicycles.     
    hull_lockable = None
    point = None
    city = None
   
    def __init__(self, bicycle_stand, namespaces):
        self.name = {}
        self.model = bicycle_stand.find(f"{{{namespaces['GIS']}}}Malli").text
        katu_name = bicycle_stand.find(f"{{{namespaces['GIS']}}}Katuosa_nimi")
        viher_name = bicycle_stand.find(f"{{{namespaces['GIS']}}}Viherosa_nimi")
        name = None
        
        if katu_name != None:
            name = katu_name.text
        if viher_name != None:
            name = viher_name.text
        
        num_stands = bicycle_stand\
            .find(f"{{{namespaces['GIS']}}}Lukumaara")
  
        if num_stands != None:
            self.number_of_stands = int(num_stands.text)
        num_places = bicycle_stand\
            .find(f"{{{namespaces['GIS']}}}Pyorapaikkojen_lukumaara")
       
        if num_places != None:
            self.number_of_places = int(num_places.text)
       
        lockable_str  = bicycle_stand\
            .find(f"{{{namespaces['GIS']}}}Pyorapaikkojen_laatutaso")

        if lockable_str: 
            self.hull_lockable = self.HULL_LOCKABLE_MAPPINGS[lockable_str.text]        
        breakpoint()
        geometry = bicycle_stand.find(f"{{{namespaces['GIS']}}}Geometry")
        point = geometry.find(f"{{{namespaces['gml']}}}Point")
        pos = point.find(f"{{{namespaces['gml']}}}pos").text.split(" ")
        
        self.point = Point(float(pos[0]), float(pos[1]), srid=SOURCE_DATA_SRID)
        self.name["fi"] = name
        # Query for the street to get translated names
        try:
            street = Street.objects.get(name=name)
        except Street.DoesNotExist:
            self.name["sv"] = name
            self.name["en"] = name
        else:
            self.name["sv"] = street.name_sv
            self.name["en"] = street.name_en
        print(self.name)
        # breakpoint()
        # addr =Address.objects.annotate(distance=Distance("location", self.point)).order_by("distance").first()
        #breakpoint()
        self.city = get_municipality_name(self.point)


def get_bicycle_stand_objects(json_data=None):
    namespaces = {"gml":"http://www.opengis.net/gml", "GIS":"http://www.tekla.com/schemas/GIS"}

    response = requests.get(URL)
    assert response.status_code == 200, "Fetching {} status code: {}".\
        format(URL, response.status_code)
    gml = ET.fromstring(response.content)
    find_str = f"{{{namespaces['gml']}}}featureMember"
    feature_members = gml.findall(find_str)
    bicycle_stands = []
    for feature_member in feature_members:
        bicycle_stand = feature_member.find(f"{{{namespaces['GIS']}}}Polkupyoraparkki")
        id = bicycle_stand.find(f"{{{namespaces['GIS']}}}Id").text
        if id == "0":            
            continue
        bicycle_stands.append(BicyleStand(bicycle_stand, namespaces))
    return bicycle_stands


class BicycleStandImporter:

    SERVICE_ID = settings.BICYCLE_STANDS_IDS["service"]
    SERVICE_NODE_ID = settings.BICYCLE_STANDS_IDS["service_node"]
    UNITS_ID_OFFSET = settings.BICYCLE_STANDS_IDS["units_offset"]
    SERVICE_NODE_NAME = "Polkupyöräparkit"
    SERVICE_NAME = "Polkupyöräparkki"
    
    SERVICE_NODE_NAMES = {
        "fi": SERVICE_NODE_NAME,
        "sv": "Cykelställningar",
        "en": "Bicycle stands"
    }    
    SERVICE_NAMES = {
        "fi": SERVICE_NAME,
        "sv": "Cykelställning",
        "en": "Bicycle stand"
    }
    def __init__(self, logger=None, root_service_node_name=None, test_data=None):
        self.logger = logger
        self.root_service_node_name = root_service_node_name
        self.test_data = test_data

    def import_bicycle_stands(self):
        service_id = self.SERVICE_ID
        self.logger.info("Importing Bicycle Stands...")
        # Delete all Bicycle stand units before storing, to ensure stored data is up-to-date.  
        Unit.objects.filter(services__id=service_id).delete()     
        filtered_objects = get_bicycle_stand_objects(json_data=self.test_data)
        for i, data_obj in enumerate(filtered_objects):
            unit_id = i + self.UNITS_ID_OFFSET          
            obj = Unit(id=unit_id)            
            point = data_obj.point
            set_field(obj, "location", point)  
            set_tku_translated_field(obj, "name", data_obj.name)
     
            #Unit.objects.filter(location__distance_lt=(point, D(m=1000)))  
            extra = {}
            extra["model"] = data_obj.model
            extra["number_of_stands"] = data_obj.number_of_stands
            extra["number_of_places"] = data_obj.number_of_places
            extra["hull_lockable"] = data_obj.hull_lockable
            set_field(obj, "extra", extra) 
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                self.logger.warning(
                    'Service "{}" does not exist!'.format(service_id)
                )
                continue
            UnitServiceDetails.objects.get_or_create(unit=obj, service=service)
            service_nodes = ServiceNode.objects.filter(related_services=service)
            obj.service_nodes.add(*service_nodes)  
            set_field(obj, "root_service_nodes", obj.get_root_service_nodes()[0])
            municipality = get_municipality(data_obj.city)
            set_field(obj, "municipality", municipality)  
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
        update_service_node_counts()
        
        #breakpoint()




def import_bicycle_stands(**kwargs):
    importer = BicycleStandImporter(**kwargs)
    create_service_node(
        importer.SERVICE_NODE_ID,
        importer.SERVICE_NODE_NAME,
        importer.root_service_node_name, 
        importer.SERVICE_NODE_NAMES
    )
    create_service(
        importer.SERVICE_ID,   
        importer.SERVICE_NODE_ID,
        importer.SERVICE_NAME, 
        importer.SERVICE_NAMES     
    )
    importer.import_bicycle_stands()
