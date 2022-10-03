from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

DEFAULT_SRID = 4326


class MaintenanceUnit(models.Model):
    unit_id = models.PositiveIntegerField(default=0)

    def __str__(self):
        return "%s" % (self.unit_id)


class MaintenanceWork(models.Model):
    point = models.PointField(srid=4326)
    events = ArrayField(models.CharField(max_length=64), default=list)
    timestamp = models.DateTimeField()
    maintenance_unit = models.ForeignKey(
        "MaintenanceUnit",
        on_delete=models.CASCADE,
        related_name="maintenance_unit",
        null=True,
    )

    def __str__(self):
        return "%s %s" % (self.timestamp, self.events)

    class Meta:
        ordering = ["-timestamp"]
