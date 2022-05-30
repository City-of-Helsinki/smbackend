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
        ordering = ["id"]

    def __str__(self):
        return self.name


class ContentType(BaseType):
    """
    Every MobileUnit has a ContetType, it describes the type,
    and gives a way to identify MobileUnits by their types. The
    ContentType is bound to the data source.
    """

    CHARGING_STATION = "CGS"
    GAS_FILLING_STATION = "GFS"
    CULTURE_ROUTE_UNIT = "CRU"
    CULTURE_ROUTE_GEOMETRY = "CRG"
    BICYCLE_STAND = "BIS"
    PAYMENT_ZONE = "PAZ"
    SPEED_LIMIT_ZONE = "SLZ"
    SCOOTER_PARKING = "SPG"
    SCOOTER_SPEED_LIMIT = "SSL"
    SCOOTER_NO_PARKING = "SNP"
    ACCESSORY_PUBLIC_TOILET = "APT"
    ACCESSORY_BENCH = "ABH"
    ACCESSORY_TABLE = "ATE"
    ACCESSORY_FURNITURE_GROUP = "AFG"
    BIKE_SERVICE_STATION = "BSS"
    SHARE_CAR_PARKING_PLACE = "SCP"

    CONTENT_TYPES = [
        (CHARGING_STATION, "ChargingStation"),
        (GAS_FILLING_STATION, "GasFillingStation"),
        (CULTURE_ROUTE_UNIT, "CultureRouteUnit"),
        (CULTURE_ROUTE_GEOMETRY, "CultureRouteGeometry"),
        (BICYCLE_STAND, "BicycleStand"),
        (PAYMENT_ZONE, "PaymentZone"),
        (SPEED_LIMIT_ZONE, "SpeedLimitZone"),
        (SCOOTER_PARKING, "ScooterParking"),
        (SCOOTER_SPEED_LIMIT, "ScooterSpeedLimit"),
        (SCOOTER_NO_PARKING, "ScooterNoParking"),
        (ACCESSORY_PUBLIC_TOILET, "AccessoryPublicToilet"),
        (ACCESSORY_BENCH, "AccessoryBench"),
        (ACCESSORY_TABLE, "AccessoryTable"),
        (ACCESSORY_FURNITURE_GROUP, "AccessoryFurnitureGroup"),
        (BIKE_SERVICE_STATION, "BikeServiceStation"),
        (SHARE_CAR_PARKING_PLACE, "ShareCarParkingPlace"),
    ]
    type_name = models.CharField(max_length=3, choices=CONTENT_TYPES, null=True)


class GroupType(BaseType):
    """
    Every MobileUnitGroup has a GroupType, it descriptes the type,
    and gives a way to identify MobileUnitGroups by their types.
    """

    CULTURE_ROUTE = "CRE"

    GROUP_TYPES = [
        (CULTURE_ROUTE, "CULTURE_ROUTE"),
    ]
    type_name = models.CharField(max_length=3, choices=GROUP_TYPES, null=True)
