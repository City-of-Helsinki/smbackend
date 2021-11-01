import uuid
from django.contrib.gis.db import models

class BaseType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=64, null=True)
    class_name = models.CharField(
        max_length=64, null=True, verbose_name="Name of the content class"
    )
    description = models.TextField(
        null=True, verbose_name="Optional description of the content type."
    )

    class Meta:
        abstract = True


class ContentType(BaseType):
    """
    Every MobileUnit has a ContetType, it descriptes the type,
    and gives a way to identify MobileUnit by their types.
    """
    CHARGING_STATION = "CGS"
    GAS_FILLING_STATION = "GFS"
    CONTENT_TYPES = {
        CHARGING_STATION: "ChargingStation",
        GAS_FILLING_STATION: "GasFillingStation",
    }
    type_name = models.CharField(
        max_length=3, 
        choices=[(k,v) for k,v in CONTENT_TYPES.items()], 
        null=True
    )


class GroupType(BaseType):
    """
    Every MobileUnitGroup has a GroupType, it descriptes the type,
    and gives a way to identify MobileUnitGroups by their types.
    """
    EXAMPLE_GROUP = "EGP"

    GROUP_TYPES = {
        EXAMPLE_GROUP: "ExampleGroup",
    }
    type_name = models.CharField(
        max_length=3, 
        choices= [(k,v) for k,v in GROUP_TYPES.items()], 
        null=True
    )