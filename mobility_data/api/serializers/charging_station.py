from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from . import UnitInfoSerializer
from ...models import(
    MobileUnit,
    ChargingStationContent,
)


class ChargingStationContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChargingStationContent
        fields = [
#            "name",
            #"address",
            "url",
            "charger_type",            
            ]


class ChargingStationSerializer(GeoFeatureModelSerializer):
    charging_station_content = ChargingStationContentSerializer(many=False, read_only=True)
    
    class Meta:
        model = MobileUnit
        geo_field = "geometry"
        fields = [
            "geometry",
            "charging_station_content",
        ]
