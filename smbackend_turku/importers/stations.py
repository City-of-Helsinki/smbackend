from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
import pytz
from functools import lru_cache
from django.conf import settings
from munigeo.models import Municipality
from mobility_data.importers.gas_filling_station import (
    get_filtered_gas_filling_station_objects  
)
from mobility_data.importers.charging_stations import(
   get_filtered_charging_station_objects
)
from services.management.commands.services_import.services import (
    update_service_node_counts,  
)   
from smbackend_turku.importers.utils import (   
    set_field,
    set_tku_translated_field,
)
from services.models import (
    Service,
    ServiceNode,
    Unit,   
    UnitServiceDetails,
)

UTC_TIMEZONE = pytz.timezone("UTC")
LANGUAGES = [language[0] for language in settings.LANGUAGES]
SOURCE_DATA_SRID = 4326

@lru_cache(None)
def get_municipality(name):
    try:
        return Municipality.objects.get(name=name)
    except Municipality.DoesNotExist:
        return None

def create_language_dict(value):
    """
    Helper function that generates a dict with elements for every language with
    the value given as parameter.
    :param value: the value to be set for all the languages
    :return: the dict
    """
    lang_dict = {}
    for lang in LANGUAGES:
        lang_dict[lang] = value
    return lang_dict

# def get_first_available_id(model, offset):
#     """
#     Find the highest unit id and add 1. This ensures that we get unique ids.
#     :param model: the model class
#     :return: the highest available id.
#     """
#     queryset = model.objects.all()
#     if queryset.count() > 0:
#         return model.objects.all().order_by("-id")[0].id+1
#     else:
#         # This branch is evaluated only when running tests
#         return 100000

def create_service_node(service_node_id, name, parent_name, service_node_names):
    """
    Creates service_node with given name and id if it does not exist. 
    Sets the parent service_node and name fields.
    :param service_node_id: the id of the service_node to be created.
    :param name: name of the service_node.
    :param parent_name: name of the parent service_node, if None the service_node will be
     topmost in the tree hierarchy.
    :param service_node_names: dict with names in all languages   
    """
    service_node = None
    try:
        service_node = ServiceNode.objects.get(id=service_node_id,name=name)       
    except ServiceNode.DoesNotExist:    
        service_node = ServiceNode(id=service_node_id)

    if parent_name: 
        try:
            parent = ServiceNode.objects.get(name=parent_name)      
        except ServiceNode.DoesNotExist:
            raise ObjectDoesNotExist("Parent ServiceNode name: {} not found.".format(parent_name))
    else:
        # The service_node will be topmost in the tree structure
        parent = None

    service_node.parent = parent
    set_tku_translated_field(service_node, "name", service_node_names)
    service_node.last_modified_time = datetime.now(UTC_TIMEZONE)
    service_node.save()
            
def create_service(service_id, service_node_id, service_name, service_names):  
    """
    Creates service with given service_id and name if it does not exist. 
    Adds the service to the given service_node and sets the name fields.
    :param service_id: the id of the service.
    :param service_node_id: the id of the service_node to which the service will have a relation
    :param service_name: name of the service
    :param service_names: dict with names in all languages
    """
    service = None
    try:
        service = Service.objects.get(id=service_id,name=service_name)
    except Service.DoesNotExist:    
        service = Service(id=service_id, clarification_enabled=False, period_enabled=False)   
        set_tku_translated_field(service, "name", service_names)     
        service_node = ServiceNode(id=service_node_id)
        service_node.related_services.add(service_id)
        service.last_modified_time = datetime.now(UTC_TIMEZONE)
        service.save()    


class GasFillingStationImporter:

    SERVICE_ID = settings.GAS_FILLING_STATIONS_IDS["service"]
    SERVICE_NODE_ID = settings.GAS_FILLING_STATIONS_IDS["service_node"]
    UNITS_ID_OFFSET = settings.GAS_FILLING_STATIONS_IDS["units_offset"]

    SERVICE_NODE_NAME = "Kaasutankkausasemat"
    SERVICE_NAME = "Kaasutankkausasema"
    SERVICE_NODE_NAMES = {
        "fi": SERVICE_NODE_NAME,
        "sv": "Gas stationer",
        "en": "Gas filling stations"
    }
    
    SERVICE_NAMES = {
        "fi": SERVICE_NAME,
        "sv": "Gas station",
        "en": "Gas filling station"
    }

    def __init__(self, logger=None, root_service_node_name=None, test_data=None):
        self.logger = logger
        self.root_service_node_name = root_service_node_name
        self.test_data = test_data

    def import_gas_filling_stations(self):
        service_id = self.SERVICE_ID
        self.logger.info("Importing gas filling stations...")
        # Delete all gas filling station units before storing, to ensure stored data is up-to-date.  
        Unit.objects.filter(services__id=service_id).delete()     
        filtered_objects = get_filtered_gas_filling_station_objects(json_data=self.test_data)
        for i, data_obj in enumerate(filtered_objects):
            unit_id = i + self.UNITS_ID_OFFSET          
            obj = Unit(id=unit_id)            
            point = data_obj.point
            point.transform(SOURCE_DATA_SRID)
            set_field(obj, "location", point)    
            set_tku_translated_field(obj, "name",\
                create_language_dict(data_obj.name))
            set_tku_translated_field(obj, "street_address",\
                create_language_dict(data_obj.street_address))
            set_tku_translated_field(obj, "address_postal_full",\
                create_language_dict(data_obj.address_postal_full))
            set_field(obj, "address_zip", data_obj.zip_code)           
            description = "{} {}".format(data_obj.operator, data_obj.lng_cng)            
            set_tku_translated_field(obj, "description",\
                create_language_dict(description))
            extra = {}
            extra["operator"] = data_obj.operator
            extra["lng_cng"] = data_obj.lng_cng
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
  

class ChargingStationImporter():

    SERVICE_ID = settings.CHARGING_STATIONS_IDS["service"]
    SERVICE_NODE_ID = settings.CHARGING_STATIONS_IDS["service_node"]
    UNITS_ID_OFFSET = settings.CHARGING_STATIONS_IDS["units_offset"]  

    SERVICE_NODE_NAME = "Sähkölatausasemat"
    SERVICE_NAME = "Sähkölatausasema"
    SERVICE_NODE_NAMES = {
        "fi": SERVICE_NODE_NAME,
        "sv": "Laddplatser",
        "en": "Charging stations"
    }
    SERVICE_NAMES = {
        "fi": SERVICE_NAME,
        "sv": "Laddplats",
        "en": "Charging station"
    }

    def __init__(self, logger=None, importer=None, root_service_node_name=None, test_data=None):
        self.logger = logger
        self.importer = importer
        self.root_service_node_name = root_service_node_name
        self.test_data = test_data

    def import_charging_stations(self):
        self.logger.info("Importing charging stations...")
        service_id = self.SERVICE_ID
        # Delete all charging station units before storing, to ensure stored data is up-to-date.  
        Unit.objects.filter(services__id=service_id).delete()
        filtered_objects = get_filtered_charging_station_objects(json_data=self.test_data)
       
        for i, data_obj in enumerate(filtered_objects):
            unit_id = i + self.UNITS_ID_OFFSET
            obj = Unit(id=unit_id)           
            point = data_obj.point
            point.transform(SOURCE_DATA_SRID)
            set_field(obj, "location", point)    
            set_tku_translated_field(obj, "name",\
                create_language_dict(data_obj.name))
            set_tku_translated_field(obj, "street_address",\
                create_language_dict(data_obj.street_address))
            set_tku_translated_field(obj, "address_postal_full",\
                create_language_dict(data_obj.address_postal_full))
            set_field(obj, "address_zip", data_obj.zip_code)
            description = "Type: {} {}kW count:{} operator:{}".format(
                data_obj.charger_type, data_obj.power, 
                data_obj.count, data_obj.operator)  
            set_tku_translated_field(obj, "description",\
                create_language_dict(description))
            extra = {}
            extra["charger_type"] = data_obj.charger_type
            extra["power"] = data_obj.power
            extra["count"] = data_obj.count 
            extra["operator"] = data_obj.operator       
            set_field(obj, "extra", extra) 
            set_field(obj, "www", data_obj.url)

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
       
    
def import_gas_filling_stations(**kwargs):    
    importer = GasFillingStationImporter(**kwargs) 
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
        importer.SERVICE_NAMES,          
 
    )
    importer.import_gas_filling_stations()


def import_charging_stations(**kwargs):
    importer = ChargingStationImporter(**kwargs)
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
    importer.import_charging_stations()
