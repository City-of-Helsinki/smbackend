from os import mkdir, listdir, remove
from os.path import isfile, join, exists
import json
from django.conf import settings
from django.contrib import admin
from django.contrib.gis.geos import LineString
from django.contrib import messages

from django.http.response import HttpResponse
from .models import (
    BicycleNetwork, 
    BicycleNetworkSource,
    BicyceNetworkPart
)

SOURCE_DATA_SRID = 3877
UPLOAD_TO = BicycleNetworkSource.UPLOAD_TO
PATH = settings.MEDIA_ROOT+"/"+UPLOAD_TO+"/"
FILTERED_PATH = PATH + "/filtered/"
   
INCLUDED_PROPERTIES = [
    "fid",
    "pituus",
    "guid",
    "oid_tunnus",
    "ketju_oid",
]

def delete_uploaded_files():
    [remove(PATH+f) for f in listdir(PATH) if isfile(join(PATH, f))]

def delete_filtered_file(name):
    remove(FILTERED_PATH+name+".geojson")

def filter_geojson(geojson_data):
    out_geojson = {}
    try:
        out_geojson["type"] = geojson_data["type"]
        out_geojson["name"] = geojson_data["name"]
        out_geojson["crs"] = geojson_data["crs"]
        out_geojson["features"] = {}
        features = []
        for feature_data in geojson_data["features"]:
            feature = {}
            feature["type"] = "Feature"
            properties_data = feature_data["properties"]    
            properties = {}
            for prop in INCLUDED_PROPERTIES:
                properties[prop] = properties_data[prop]
            feature["properties"] = properties
            feature["geometry"] = feature_data["geometry"]
            features.append(feature)
    except KeyError:
        return False, None
    out_geojson["features"] = features
    return True, out_geojson


def save_network_to_db(geojson_data, network_name):
    # BicycleNetwork.objects.all().delete()
    # return
    BicycleNetwork.objects.filter(name=network_name).delete()
    network = BicycleNetwork.objects.create(name=network_name)
    features = geojson_data["features"]
    for feature in features:
        part = BicyceNetworkPart.objects.create(bicycle_network=network)
        for prop in INCLUDED_PROPERTIES:
            setattr(part, prop, feature["properties"][prop])
        coords = feature["geometry"]["coordinates"] 
        try:
            part.geometry = LineString(coords, srid=SOURCE_DATA_SRID) 
        except:
            print("Dimension mismatch: "+str(feature))
        part.save()

def process_file_obj(file_obj, name):
        
        with open(file_obj.path, "r") as file:
            try:
                geojson_data = json.loads(file.read())
            except json.decoder.JSONDecodeError:
                return False

        success, filtered_geojson = filter_geojson(geojson_data)
        if not success:
            return False

        if not exists(FILTERED_PATH):
            mkdir(FILTERED_PATH)
        save_network_to_db(filtered_geojson, name)
        with open(FILTERED_PATH+name+".geojson", "w") as file:
            json.dump(filtered_geojson, file)
        
        return True


class BicycleNetworkSourceAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Limit number of instances to One as BicycleNetwrokSource is a 
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

            if "main_network-clear" in request.POST:
                delete_filtered_file(BicycleNetworkSource.MAIN_NETWORK_NAME)
                BicycleNetwork.objets.filter(name=BicycleNetworkSource.MAIN_NETWORK_NAME).delete()   
            if "local_network-clear" in request.POST:
                delete_filtered_file(BicycleNetworkSource.LOCAL_NETWORK_NAME)
                BicycleNetwork.objects.filter(name=BicycleNetworkSource.LOCAL_NETWORK_NAME).delete() 
            if "quality_lanes-clear" in request.POST:
                delete_filtered_file(BicycleNetworkSource.QUALITY_LANES_NAME)
                BicycleNetwork.objects.filter(name=BicycleNetworkSource.QUALITY_LANES_NAME).delete()   

            delete_uploaded_files()
            if not success:
                messages.error(request, "Invalid GEOJSON.")

        return super().response_change(request, obj)


admin.site.register(BicycleNetworkSource, BicycleNetworkSourceAdmin)
