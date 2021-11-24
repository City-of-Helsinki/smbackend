from os import mkdir, listdir, remove
from os.path import isfile, join, exists
import json
import logging
from django.conf import settings
from django.contrib import admin
from django.contrib.gis.geos import LineString
from django.contrib import messages
from .models import (
    BicycleNetwork, 
    BicycleNetworkSource,
    BicycleNetworkPart
)

logger = logging.getLogger("bicycle_network")
SOURCE_DATA_SRID = 3877
CONVERT_TO_SRID = 4326 # if None, No transformations are made and SOURCE_DATA_SRID is used.
UPLOAD_TO = BicycleNetworkSource.UPLOAD_TO
PATH = f"{settings.MEDIA_ROOT}/{UPLOAD_TO}/"
FILTERED_PATH = f"{PATH}/filtered/"
# List of properties to include and the type for typecasting   
INCLUD_PROPERTIES = [
  ("toiminnall", int),
  ("liikennevi", int),
  ("teksti", str),
  ("tienim2", str),
  ("TKU_toiminnall_pp", int),
]

def delete_uploaded_files():
    [remove(PATH+f) for f in listdir(PATH) if isfile(join(PATH, f))]

def delete_filtered_file(name):
    remove(f"{FILTERED_PATH}{name}.geojson")

def filter_geojson(input_geojson):
    """
    Filters the input_geojson, preservs only properties set in the
    INCLUD_PROPERTIES. If CONVERT_TO_SRID is set, transforms geometry
    to given srid. 
    """
    out_geojson = {}
    try:
        out_geojson["type"] = input_geojson["type"]
        out_geojson["name"] = input_geojson["name"]
        if not CONVERT_TO_SRID:
            out_geojson["crs"] = input_geojson["crs"]
        out_geojson["features"] = {}
        features = []
        for feature_data in input_geojson["features"]:
            feature = {}
            feature["type"] = "Feature"
            properties_data = feature_data["properties"]    
            properties = {}
            
            for prop_name, type_class in INCLUD_PROPERTIES:
                prop = properties_data.get(prop_name,None)
                if prop:
                    properties[prop_name] = type_class(prop)
                else:
                    properties[prop_name] = None                    
            feature["properties"] = properties

            if CONVERT_TO_SRID:
                try:
                    coords = feature_data["geometry"]["coordinates"]
                    ls = LineString(coords, srid=SOURCE_DATA_SRID)                
                    ls.transform(CONVERT_TO_SRID)
                    feature_data["geometry"]["coordinates"] = ls.coords
                except TypeError as err:                    
                    logger.warning(err)
                    continue
            # geom = feature_data.get("geometry", None)
            # if geom == None:
            #     print("HERE")
            feature["geometry"] = feature_data["geometry"]
            features.append(feature)
            
    except KeyError:
        return False, None
    out_geojson["features"] = features
    return True, out_geojson


def save_network_to_db(input_geojson, network_name):
    # BicycleNetwork.objects.all().delete()
    # return
    BicycleNetwork.objects.filter(name=network_name).delete()
    network = BicycleNetwork.objects.create(name=network_name)
    features = input_geojson["features"]
    for feature in features:
        part = BicycleNetworkPart.objects.create(bicycle_network=network)
        for prop_name, _ in INCLUD_PROPERTIES:
            setattr(part, prop_name, feature["properties"][prop_name])
        coords = feature["geometry"]["coordinates"] 
        try:
            srid=CONVERT_TO_SRID if CONVERT_TO_SRID else SOURCE_DATA_SRID             
            part.geometry = LineString(coords, srid=srid) 
        except TypeError as err:
            logger.warning(err)
        part.save()


def process_file_obj(file_obj, name):  
    
    with open(file_obj.path, "r") as file:
        try:
            input_geojson = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            return False

    success, filtered_geojson = filter_geojson(input_geojson)
    if not success:
        return False

    if not exists(FILTERED_PATH):
        mkdir(FILTERED_PATH)
    save_network_to_db(filtered_geojson, name)
    with open(FILTERED_PATH+name+".geojson", "w") as file:
        json.dump(filtered_geojson, file, ensure_ascii=False)
    
    return True


class BicycleNetworkSourceAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        # Limit number of instances to One as BicycleNetworkSource is a 
        # singleton class.
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def response_change(self, request, obj):
        if "_save" or "_continue" in request.POST:   
            success = True
            if "main_network" not in request.POST and isfile(obj.main_network.path):
                success = process_file_obj(obj.main_network, BicycleNetworkSource.MAIN_NETWORK_NAME)
            if "local_network" not in request.POST and isfile(obj.local_network.path):
                success = process_file_obj(obj.local_network, BicycleNetworkSource.LOCAL_NETWORK_NAME)
            if "quality_lanes" not in request.POST and isfile(obj.quality_lanes.path):
                success = process_file_obj(obj.quality_lanes, BicycleNetworkSource.QUALITY_LANES_NAME)
            # Delete actions
            if "main_network-clear" in request.POST:
                delete_filtered_file(BicycleNetworkSource.MAIN_NETWORK_NAME)
                BicycleNetwork.objects.filter(name=BicycleNetworkSource.MAIN_NETWORK_NAME).delete()   
            if "local_network-clear" in request.POST:
                delete_filtered_file(BicycleNetworkSource.LOCAL_NETWORK_NAME)
                BicycleNetwork.objects.filter(name=BicycleNetworkSource.LOCAL_NETWORK_NAME).delete() 
            if "quality_lanes-clear" in request.POST:
                delete_filtered_file(BicycleNetworkSource.QUALITY_LANES_NAME)
                BicycleNetwork.objects.filter(name=BicycleNetworkSource.QUALITY_LANES_NAME).delete()   

            delete_uploaded_files()
            if not success:
                messages.error(request, "Invalid Input GEOJSON.")

        return super().response_change(request, obj)


admin.site.register(BicycleNetworkSource, BicycleNetworkSourceAdmin)
