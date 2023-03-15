from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from street_maintenance.management.commands.constants import PROVIDER_CHOICES

DEFAULT_SRID = 4326


class MaintenanceUnit(models.Model):

    unit_id = models.CharField(max_length=64, null=True)
    provider = models.CharField(max_length=16, choices=PROVIDER_CHOICES, null=True)
    names = ArrayField(models.CharField(max_length=64), default=list)

    def __str__(self):
        return "%s" % (self.unit_id)


class MaintenanceWork(models.Model):
    geometry = models.GeometryField(srid=DEFAULT_SRID, null=True)
    events = ArrayField(models.CharField(max_length=64), default=list)
    original_event_names = ArrayField(models.CharField(max_length=64), default=list)
    timestamp = models.DateTimeField()
    maintenance_unit = models.ForeignKey(
        "MaintenanceUnit",
        on_delete=models.CASCADE,
        related_name="maintenance_work",
        null=True,
    )

    def __str__(self):
        return "%s %s" % (self.timestamp, self.events)

    class Meta:
        ordering = ["-timestamp"]


class GeometryHistory(models.Model):
    timestamp = models.DateTimeField()
    geometry = models.GeometryField(srid=DEFAULT_SRID, null=True)
    coordinates = ArrayField(ArrayField(models.FloatField()), default=list)
    events = ArrayField(models.CharField(max_length=64), default=list)
    provider = models.CharField(max_length=16, choices=PROVIDER_CHOICES, null=True)

    def __str__(self):
        return "%s %s" % (self.timestamp, self.events)

    class Meta:
        ordering = ["-timestamp"]
