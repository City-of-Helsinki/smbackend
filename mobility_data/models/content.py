import uuid
from django.contrib.gis.db import models
from django.contrib.contenttypes.fields import GenericRelation
from . import MobileUnit


class BaseStation(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    
    class Meta:
        abstract = True


class ChargingStationContent(BaseStation):
    url = models.URLField(null=True)
    charger_type = models.CharField(max_length=32, null=True)
    mobile_unit = models.OneToOneField(
        MobileUnit, 
        related_name="charging_station_content",
        on_delete=models.CASCADE, 
    )
 

class GasFillingStationContent(BaseStation):
    lng_cng = models.CharField(max_length=8, null=True)
    operator = models.CharField(max_length=32, null=True)  
    mobile_unit = models.OneToOneField(
        MobileUnit, 
        related_name="gas_filling_station_content",
        on_delete=models.CASCADE, 
    )


