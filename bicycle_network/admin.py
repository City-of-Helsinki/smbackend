import json
import logging
from os import listdir, remove
from os.path import isfile, join

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import LineString, MultiLineString
from shapely import geometry, ops
from shapely.geometry import mapping

from .models import BicycleNetwork, BicycleNetworkPart

logger = logging.getLogger("bicycle_network")
SRID_MAPPINGS = {
    "urn:ogc:def:crs:OGC:1.3:CRS84": 4326,
    "urn:ogc:def:crs:EPSG::3877": 3877,
}
# if None, No transformations are made and source datas srid is used.
CONVERT_TO_SRID = 4326

# GK25_SRID is used to transform linestrings to, to calculate the length,
# as the Unit for 3879 is metre, in 4326 the Unit is degrees.
GK25_SRID = 3879
GK25_SRS = SpatialReference(GK25_SRID)
SOURCE_SRS = SpatialReference(CONVERT_TO_SRID)
coord_transform = CoordTransform(SOURCE_SRS, GK25_SRS)

UPLOAD_TO = BicycleNetwork.UPLOAD_TO
PATH = f"{settings.MEDIA_ROOT}/{UPLOAD_TO}/"


def delete_uploaded_files():
    """
    Deletes all files in PATH.
    """
    [remove(PATH + f) for f in listdir(PATH) if isfile(join(PATH, f))]


def get_source_data_srid(crs_field):
    souce_data_srid = SRID_MAPPINGS.get(
        crs_field["properties"]["name"], CONVERT_TO_SRID
    )
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


def merge_linestrings(input_geojson, request):
    """
    Combnes linestrings who are connected using shapely.
    """
    features = input_geojson["features"]
    lines = []
    success = True
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
    num_coords = 0
    for coords in geometry_data["coordinates"]:
        # If the len of coords is equal or less than 2 we know
        # that the merge of linestrings has failed and we break out.
        if len(coords) <= 2:
            success = False
            features = input_geojson["features"]
            break
        feature = {}
        feature["properties"] = {}
        feature["type"] = "Feature"
        geometry_elem = {}
        geometry_elem["type"] = "LineString"
        geometry_elem["coordinates"] = coords
        feature["geometry"] = geometry_elem
        features.append(feature)
        num_coords += 1
    input_geojson["features"] = features
    msg = f"Merged {len(multi_line.geoms)} LineStrings to {num_coords} LineStrings."
    logger.info(msg)
    if success:
        messages.info(request, msg)
    return success, input_geojson


def filter_geojson(input_geojson):
    """
    Filters the input_geojson, skips all the properties.
    If CONVERT_TO_SRID is set, transforms geometry
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
            try:
                geom_type = feature_data["geometry"]["type"]
                coords = feature_data["geometry"]["coordinates"]
                geom = None
                if geom_type == "LineString":
                    geom = LineString(coords, srid=source_data_srid)
                elif geom_type == "MultiLineString":
                    # If num features == 1 we know that it is merged.
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
        # file. We return False to indicate the error.
        return False, None
    out_geojson["features"] = features
    return True, out_geojson, merged_multilinestring


def save_network_to_db(input_geojson, obj_id):
    # Completly delete the network and its parts before storing it,
    # to ensure the data stored will be up to date. By deleting the
    # bicycle network the parts referencing to it will also be deleted.
    network = BicycleNetwork.objects.get(id=obj_id)
    BicycleNetworkPart.objects.filter(bicycle_network=network).delete()
    features = input_geojson["features"]
    length = 0
    # Every feature in the input_geojson will be stored as a BicycleNetworkPart.
    for feature in features:
        part = BicycleNetworkPart.objects.create(bicycle_network=network)
        coords = feature["geometry"]["coordinates"]
        srid = (
            CONVERT_TO_SRID
            if CONVERT_TO_SRID
            else get_source_data_srid(input_geojson["crs"])
        )
        geom_type = feature["geometry"]["type"]

        if geom_type == "LineString":
            part.geometry = LineString(coords, srid=srid)

        elif geom_type == "MultiLineString":
            part.geometry = create_multilinestring(coords, srid)
        part.save()
        part.geometry.transform(coord_transform)
        length += part.geometry.length
    network.length = round(length, 2)
    network.save()


def process_file_obj(obj, request):
    """
    This function Opens the uploaded file, calls the filter function
    and finally stores the filtered data to the db and file.
    """
    with open(obj.file.path, "r") as file:
        try:
            input_geojson = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            return False

    merge_success, filtered_geojson, merged_linestring = filter_geojson(input_geojson)
    # If not merged_multilinestring we can try to merge the linestring that overlaps.
    if not merged_linestring:
        merge_success, merged_geojson = merge_linestrings(filtered_geojson, request)

    save_network_to_db(merged_geojson, obj.id)
    if not merge_success:
        messages.warning(
            request, "Merging of linestrings failed, saved without merging."
        )
    # Do not save any files after the database is populated.
    delete_uploaded_files()
    return True


class BicycleNetworkAdmin(admin.ModelAdmin):
    list_display = ("name",)
    readonly_fields = ("length",)

    def name(self, obj):
        if obj.name is None:
            return "Anonymous"
        else:
            return obj.name

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.file:
            if isfile(obj.file.path):
                success = process_file_obj(obj, request)
                if not success:
                    messages.error(
                        request, "Invalid Input GEOJSON or format not supported."
                    )


admin.site.register(BicycleNetwork, BicycleNetworkAdmin)
