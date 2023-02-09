import uuid

from django.conf import settings
from django.contrib.gis.db import models
from munigeo.models import Municipality

from . import ContentType, GroupType


class BaseUnit(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_time = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=256, null=True)
    description = models.TextField(null=True)

    class Meta:
        abstract = True
        ordering = ["-created_time"]

    def __str__(self):
        if self.name:
            return self.name
        else:
            return ""


class MobileUnitGroup(BaseUnit):
    """
    Umbrella model to order MobileUnits into groups.
    Every Group has a relation to GroupType that describes the group.
    i.e. A walkingroute group can have routedata, sights as mobile_units.
    """

    group_type = models.ForeignKey(
        GroupType, on_delete=models.CASCADE, related_name="unit_groups"
    )


class MobileUnit(BaseUnit):
    """
    MobileUnit is the base model. It contains basic information about the
    MobileUnit such as name, geometry. Eeach MobileUnit has a relation to a
    ContentType that describes the specific type of the unit. MobileUnits
    can also have a relation to a UnitGroup. The extra field can contain
    data that are specific for a data source.
    """

    geometry = models.GeometryField(srid=settings.DEFAULT_SRID, null=True)
    address = models.CharField(max_length=100, null=True)
    municipality = models.ForeignKey(
        Municipality, null=True, db_index=True, on_delete=models.CASCADE
    )
    address_zip = models.CharField(max_length=10, null=True)

    content_types = models.ManyToManyField(ContentType, related_name="mobile_units")
    unit_id = models.IntegerField(
        null=True,
        verbose_name="optional id to a unit in the servicemap, if id exist data is serialized from services_unit table",
    )
    mobile_unit_group = models.ForeignKey(
        MobileUnitGroup,
        on_delete=models.CASCADE,
        null=True,
        related_name="mobile_units",
    )
    extra = models.JSONField(null=True)
