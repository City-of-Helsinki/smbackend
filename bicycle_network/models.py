from django.contrib.gis.db import models


class BicycleNetwork(models.Model):
    UPLOAD_TO = "bicycle_network"

    name = models.CharField(max_length=64, null=True)
    file = models.FileField(upload_to=UPLOAD_TO, null=True)
    length = models.FloatField(null=True, blank=True, verbose_name="Length in meters.")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name


class BicycleNetworkPart(models.Model):
    """
    Stores geometry parts of the BicycleNetwork.
    """

    class Meta:
        ordering = ["-id"]

    bicycle_network = models.ForeignKey(
        BicycleNetwork, on_delete=models.CASCADE, related_name="network_part"
    )
    geometry = models.GeometryField(null=True)
