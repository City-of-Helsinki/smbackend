# from os import mkdir, listdir, remove
# from os.path import isfile, join, exists
# import json
from django.contrib.gis.db import models
# from django.contrib.gis.geos import LineString
from django.conf import settings
# SOURCE_DATA_SRID = 3877

# UPLOAD_TO = "bicycle_network"
# PATH = settings.MEDIA_ROOT+"/"+UPLOAD_TO+"/"
# FILTERED_PATH = PATH + "/filtered/"
   
# INCLUDED_PROPERTIES = [
#     "fid",
#     "pituus",
#     "guid",
#     "oid_tunnus",
#     "ketju_oid",
# ]
# def delete_uploaded_files():
#     [remove(PATH+f) for f in listdir(PATH) if isfile(join(PATH, f))]
    

# def filter_geojson(geojson_data):
#     out_geojson = {}
#     out_geojson["type"] = geojson_data["type"]
#     out_geojson["name"] = geojson_data["name"]
#     out_geojson["crs"] = geojson_data["crs"]
#     out_geojson["features"] = {}
#     features = []
#     for feature_data in geojson_data["features"]:
#         feature = {}
#         feature["type"] = "Feature"
#         properties_data = feature_data["properties"]    
#         properties = {}
#         for prop in INCLUDED_PROPERTIES:
#             properties[prop] = properties_data[prop]

#         feature["properties"] = properties
#         feature["geometry"] = feature_data["geometry"]
#         features.append(feature)
#     out_geojson["features"] = features
#     return out_geojson


# def save_network_to_db(geojson_data):
#     BicycleNetwork.objects.all().delete()
#     network = BicycleNetwork.objects.create(name=geojson_data["name"])
#     features = geojson_data["features"]
#     for feature in features:
#         part = BicyceNetworkPart.objects.create(bicycle_network=network)
#         for prop in INCLUDED_PROPERTIES:
#             setattr(part, prop, feature["properties"][prop])
#         coords = feature["geometry"]["coordinates"]  
#         part.save()

# def process_file_obj(file_obj, name):
#         filename = file_obj.url.split("/")[-1]                
#         with open(file_obj.path, "r") as file:
#             geojson_data = json.loads(file.read())
#         filtered_geojson = filter_geojson(geojson_data)
#         if not exists(FILTERED_PATH):
#             mkdir(FILTERED_PATH)
#         #save_network_to_db(filter_geojson)
#         with open(FILTERED_PATH+name+".geojson", "w") as file:
#             json.dump(filtered_geojson, file)


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class BicycleNetwork(models.Model):
    name = models.CharField(max_length=32, null=True)    


class BicycleNetworkPart(models.Model):

    class Meta:
        ordering = ["-id"]

    bicycle_network = models.ForeignKey(
        BicycleNetwork, 
        on_delete=models.CASCADE,
        related_name="network_part"
    )
    geometry = models.GeometryField(null=True)
    # Property field names are the same as in the input data.
    toiminnall = models.IntegerField(null=True, 
        verbose_name="Functional class")
    liikennevi = models.IntegerField(null=True, 
        verbose_name="Direction of trafic flow")
    teksti = models.CharField(max_length=64, null=True, 
        verbose_name="Name of the street (in Finnish)")
    tienim2 = models.CharField(max_length=64, null=True,
        verbose_name="Name of the street (in Swedish)")
    TKU_toiminnall_pp = models.IntegerField(null=True,
        verbose_name="Functional class of cycle or pedestrian path")
 


class BicycleNetworkSource(SingletonModel):
    UPLOAD_TO = "bicycle_network"
    MAIN_NETWORK_NAME = "main_network"
    LOCAL_NETWORK_NAME = "local_network"
    QUALITY_LANES_NAME = "quality_lanes"

    main_network = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
    local_network = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
    quality_lanes = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
  

    def save(self, *args, **kwargs):
        # Call save, otherwise file is not stored to the filesymes
        super(BicycleNetworkSource, self).save(*args, **kwargs)
        
        # if self.main_network and isfile(self.main_network.path):
        #     process_file_obj(self.main_network, self.MAIN_NETWORK_NAME)
        # if self.local_network and isfile(self.local_network.path):
        #     process_file_obj(self.local_network, self.LOCAL_NETWORK_NAME)
        # if self.quality_lanes and isfile(self.quality_lanes.path):
        #     process_file_obj(self.quality_lanes, self.QUALITY_LANES_NAME)

        # delete_uploaded_files()
     
  


    


