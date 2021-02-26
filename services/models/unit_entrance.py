from django.contrib.gis.db import models
from munigeo.utils import get_default_srid

from services.utils import get_translated

from .unit import Unit

PROJECTION_SRID = get_default_srid()


class UnitEntrance(models.Model):
    unit = models.ForeignKey(
        Unit, db_index=True, related_name="entrances", on_delete=models.CASCADE
    )
    is_main_entrance = models.BooleanField(default=True)
    name = models.CharField(max_length=600)
    location = models.PointField(null=True, srid=PROJECTION_SRID)
    picture_url = models.URLField(max_length=600, null=True)
    streetview_url = models.URLField(max_length=600, null=True)
    created_time = models.DateTimeField(null=True)
    last_modified_time = models.DateTimeField(
        db_index=True, help_text="Time of last modification"
    )

    class Meta:
        ordering = ["-pk", "-is_main_entrance"]

    def __str__(self):
        return "%s (%s)" % (get_translated(self, "name"), self.id)
