import uuid
from django.contrib.gis.db import models

class BaseType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=64, null=True)
    description = models.TextField(
        null=True, verbose_name="Optional description of the content type."
    )

    class Meta:
        abstract = True


class ContentType(BaseType):
    """
    Every MobileUnit has a ContetType, it describes the type,
    and gives a way to identify MobileUnits by their types. The
    ContentType is bound to the data source.
    """
    CHARGING_STATION = "CGS"
    GAS_FILLING_STATION = "GFS"
    CONTENT_TYPES = [
        (CHARGING_STATION, "ChargingStation"),
        (GAS_FILLING_STATION, "GasFillingStation"),
    ]
    type_name = models.CharField(
        max_length=3, 
        choices=CONTENT_TYPES, 
        null=True
    )


class GroupType(BaseType):
    """
    Every MobileUnitGroup has a GroupType, it descriptes the type,
    and gives a way to identify MobileUnitGroups by their types.
    """
    EXAMPLE_GROUP = "EGP"

    GROUP_TYPES = [
        (EXAMPLE_GROUP, "ExampleGroup"),
    ]
    type_name = models.CharField(
        max_length=3, 
        choices=GROUP_TYPES, 
        null=True
    )