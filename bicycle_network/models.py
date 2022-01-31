
from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString


class BicycleNetwork(models.Model):
    UPLOAD_TO = "bicycle_network" 

    name = models.CharField(max_length=32, null=True)     
    file = models.FileField(upload_to=UPLOAD_TO, null=True)
    length = models.FloatField(null=True, blank=True)    

    def __str__(self):
        return self.name

class BicycleNetworkPart(models.Model):
    """
    Stores the parts of the BicycleNetworks, geometry and properties.
    """
    class Meta:
        ordering = ["-id"]

    bicycle_network = models.ForeignKey(
        BicycleNetwork, 
        on_delete=models.CASCADE,
        related_name="network_part"
    )
    geometry = models.GeometryField(null=True)
   


# class SingletonModel(models.Model):
#     """
#     Singleton class. Classes that inherits SingletonModel can only have one 
#     instance of themselves.
#     """
#     class Meta:
#         abstract = True

#     def save(self, *args, **kwargs):
#         self.pk = 1
#         super(SingletonModel, self).save(*args, **kwargs)

#     @classmethod
#     def load(cls):
#         obj, _ = cls.objects.get_or_create(pk=1)
#         return obj




# class BicycleNetworkSource(SingletonModel):
#     """
#     Model to store the names of the uploaded files. The files are deleted
#     after they are processed and stored. Class inherits from the SingletonModel
#     class.
#     """
#     # Files will be uploaded to MEDIA.ROOT+UPLOAD_TO
#     UPLOAD_TO = "bicycle_network" 
#     MAIN_NETWORK_NAME = "main_network"
#     LOCAL_NETWORK_NAME = "local_network"
#     QUALITY_LANES_NAME = "quality_lanes"

#     main_network = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
#     local_network = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
#     quality_lanes = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
     
  


    


