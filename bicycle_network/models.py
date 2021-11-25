from django.contrib.gis.db import models


class BicycleNetwork(models.Model):
    """
    Base model for a BicycleNetwork
    """
    name = models.CharField(max_length=32, null=True)    


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
    # Property field names are equal to the input data.
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


class SingletonModel(models.Model):
    """
    Singleton class. Classes that inherits SingletonModel can only have one 
    instance of themselves.
    """
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class BicycleNetworkSource(SingletonModel):
    """
    Model to store the names of the uploaded files. The files are deleted
    after they are processed and stored. Class inherits from the SingletonModel
    class.
    """
    # Files will be uploaded to MEDIA.ROOT+UPLOAD_TO
    UPLOAD_TO = "bicycle_network" 
    MAIN_NETWORK_NAME = "main_network"
    LOCAL_NETWORK_NAME = "local_network"
    QUALITY_LANES_NAME = "quality_lanes"

    main_network = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
    local_network = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
    quality_lanes = models.FileField(upload_to=UPLOAD_TO, null=True, blank=True)
     
  


    


