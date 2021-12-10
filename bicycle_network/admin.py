from os import mkdir, listdir, remove
from os.path import isfile, join, exists
import json
import logging
from shapely import geometry, ops
from shapely.geometry import mapping
from django.conf import settings
from django.contrib import admin
from django.contrib.gis.geos import LineString, MultiLineString
from django.contrib import messages
from .models import (
    BicycleNetwork, 
    BicycleNetworkSource,
    BicycleNetworkPart
)

logger = logging.getLogger("bicycle_network")
SRID_MAPPINGS = {
    "urn:ogc:def:crs:OGC:1.3:CRS84": 4326,
    "urn:ogc:def:crs:EPSG::3877": 3877,
}
CONVERT_TO_SRID = 4326 # if None, No transformations are made and source datas srid is used.
LINESTRINGS = True
UPLOAD_TO = BicycleNetworkSource.UPLOAD_TO
PATH = f"{settings.MEDIA_ROOT}/{UPLOAD_TO}/"
# path where the filtered .geojson files will be stored
FILTERED_PATH = f"{PATH}/filtered/"
# List of properties to include and the type for typecasting   
INCLUDE_PROPERTIES = [
  ("toiminnall", int),
  ("liikennevi", int),
  ("teksti", str),
  ("tienim2", str),
  ("TKU_toiminnall_pp", int),
]

def delete_uploaded_files():
    """
    Deletes all files in PATH.
    """
    [remove(PATH+f) for f in listdir(PATH) if isfile(join(PATH, f))]

def delete_filtered_file(name):
    try:
        remove(f"{FILTERED_PATH}{name}.geojson")
        return True
    except FileNotFoundError:
        return False

def get_source_data_srid(crs_field):
    souce_data_srid =SRID_MAPPINGS.get(
        crs_field["properties"]["name"], CONVERT_TO_SRID)
    return souce_data_srid

def create_multilinestring(coords, srid):
    """
    Creates a MultiLineString from coords with the given srid.
    Coords must have to following format [[[1,1],[1,2]],[[2,2],[3,3]].
    """
    lss = []
    for coord in coords:        
        ls = LineString(coord, srid=srid)
        lss.append(ls)
    return MultiLineString(lss, srid=srid)
  
def merge_linestrings(input_geojson):
    """
    Combnes linestrings who are connected using shapely.
    """
    features = input_geojson["features"]
    lines = []
    # Create LineStrings to be merged from geojson features.
    for feature in features:
        coords = feature["geometry"]["coordinates"]
        coords_list = [list(c) for c in coords]      
        if not coords_list:
            continue
        # The input data might have coords in format: [[(2,2),(1,1)]]
        # The tuple inside the nested list is removed:
        if type(coords_list[0][0]) == tuple:
            coords_list = [[list(j) for j in i] for i in coords_list][0]   
        ls = geometry.LineString(coords_list)
        lines.append(ls)

    multi_line = geometry.MultiLineString(lines)
    merged_line = ops.linemerge(multi_line)   
    geometry_data = mapping(merged_line)
    features = []
    # Create geojson features with LineString geometrys from MultiLineString.
    for coords in geometry_data["coordinates"]:
        feature = {}
        feature["properties"] = {}
        feature["type"] = "Feature"
        geometry_elem = {}
        geometry_elem["type"] = "LineString"
        geometry_elem["coordinates"] = coords
        feature["geometry"] = geometry_elem
        features.append(feature)
    input_geojson["features"] = features  
    logger.info(f"Merged {len(multi_line)} LineStrings to {len(merged_line)} LineStrings.")
    return input_geojson    

def filter_geojson(input_geojson):
    """
    Filters the input_geojson, preservs only properties set in the
    INCLUDE_PROPERTIES. If CONVERT_TO_SRID is set, transforms geometry
    to given srid. 
    """
    out_geojson = {}
    # Flag to detect if the complete geometry is merged into One multilinestring
    merged_multilinestring = False
    try:
        out_geojson["type"] = input_geojson["type"]
        out_geojson["name"] = input_geojson["name"]
        out_geojson["crs"] = input_geojson["crs"]
        source_data_srid = get_source_data_srid(input_geojson["crs"])
        out_geojson["features"] = {}
        features = []
        for feature_data in input_geojson["features"]:
            feature = {}
            feature["type"] = "Feature"
            properties_data = feature_data["properties"]    
            properties = {}
            # Include the properties set in INCLUDE_PROPERTIES     
            for prop_name, type_class in INCLUDE_PROPERTIES:
                prop = properties_data.get(prop_name,None)
                if prop:
                    properties[prop_name] = type_class(prop)
                else:
                    properties[prop_name] = None                    
            feature["properties"] = properties

            try:
                geom_type = feature_data["geometry"]["type"]                
                coords = feature_data["geometry"]["coordinates"]
                geom = None
                if geom_type == "LineString":
                    geom = LineString(coords, srid=source_data_srid)                
                elif geom_type == "MultiLineString":
                    if len(input_geojson["features"]) == 1:
                        merged_multilinestring = True
                    geom = create_multilinestring(coords, source_data_srid)                  
               
                if source_data_srid != CONVERT_TO_SRID:
                    geom.transform(CONVERT_TO_SRID)
                feature_data["geometry"]["coordinates"] = geom.coords
            except TypeError as err:                    
                logger.warning(err)
                # If transformation is not possible, we execlude the feature
                # thus it would have errorneous data.
                continue
            
            feature["geometry"] = feature_data["geometry"]
            features.append(feature)            
    except KeyError:
        # In case a KeyError, which is probably caused by a faulty input geojson
        # file. We retrun False to indicate the error.
        return False, None
    out_geojson["features"] = features    
    return True, out_geojson, merged_multilinestring

def save_network_to_db(input_geojson, network_name):
    # Completly delete the network and its parts before storing it,
    # to ensure the data stored will be up to date. By deleting the 
    # bicycle network the parts referencing to it will also be deleted.
    BicycleNetwork.objects.filter(name=network_name).delete()
    network = BicycleNetwork.objects.create(name=network_name)
    features = input_geojson["features"]
    # Every feature in the input_geojson will be stored as a BicycleNetworkPart.
    for feature in features:
        part = BicycleNetworkPart.objects.create(bicycle_network=network)
        for prop_name, _ in INCLUDE_PROPERTIES:
            setattr(part, prop_name, feature["properties"].get(prop_name, None))
        coords = feature["geometry"]["coordinates"] 
        srid=CONVERT_TO_SRID if CONVERT_TO_SRID else get_source_data_srid(input_geojson["crs"])             
        geom_type = feature["geometry"]["type"]
        if geom_type == "LineString":
            part.geometry = LineString(coords, srid=srid)
        elif geom_type == "MultiLineString":
            part.geometry = create_multilinestring(coords, srid)
        part.save()

def process_file_obj(file_obj, name):  
    """
    This function is called when continue&save or save&quit is pressed in the
    admin. It Opens the file, calls the filter function and finally stores
    the filtered data to the db and file.
    """
    with open(file_obj.path, "r") as file:
        try:
            input_geojson = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            return False

    if not exists(FILTERED_PATH):
        mkdir(FILTERED_PATH)

    success, filtered_geojson, merged_mutlilinestring = filter_geojson(input_geojson)
    # If merged_multilinestring we can skip the merge of linestrings
    if not merged_mutlilinestring:
        filtered_geojson = merge_linestrings(filtered_geojson)
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
        # Delete actions sent in request.POST
        delete_actions = [
            "main_network-clear",
            "local_network-clear",
            "quality_lanes-clear"
        ]
        save_actions = [
            "main_network",
            "local_network",
            "quality_lanes"
        ]
        if "_save" or "_continue" in request.POST:   
            # Check for save actions
            for save_action in save_actions:
                # django admon "fuzzy" logic, if the action is Not in the request.    
                if save_action not in request.POST:
                    file = getattr(obj, save_action)
                    # Check that the uploaded file exists.
                    if isfile(file.path):
                        # get attr name.
                        attr_name = f"{(save_action.upper())}_NAME"
                        name = getattr(BicycleNetworkSource, attr_name)
                        success = process_file_obj(file, name)
                        if not success:
                            messages.error(request, "Invalid Input GEOJSON.")                  
            
            for action in request.POST:             
                # Check for delete actions.
                if action in delete_actions:
                    # get the attribute name from action.
                    attr_name = f"{(action.upper())[:-6]}_NAME"
                    name = getattr(BicycleNetworkSource, attr_name)
                    result = delete_filtered_file(name)
                    if not result:
                        messages.error(request, "File not found.")
                    BicycleNetwork.objects.filter(name=name).delete() 
       
            delete_uploaded_files()
        return super().response_change(request, obj)


admin.site.register(BicycleNetworkSource, BicycleNetworkSourceAdmin)
