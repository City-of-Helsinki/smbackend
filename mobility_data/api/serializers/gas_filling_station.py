from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from . import UnitInfoSerializer
from ...models import(
    GasFillingStationContent,
    MobileUnit
)

class GasFillingStationContentSerializer(serializers.ModelSerializer):
    name = serializers.PrimaryKeyRelatedField(many=False, source="unit.name", read_only=True)
    name_fi = serializers.PrimaryKeyRelatedField(many=False, source="unit.name", read_only=True)
    name_sv = serializers.PrimaryKeyRelatedField(many=False, source="unit.name", read_only=True)
    name_en = serializers.PrimaryKeyRelatedField(many=False, source="unit.name", read_only=True)

    class Meta:
        model = GasFillingStationContent
        fields = [
            "name",
            "name_fi",
            "name_sv",
            "name_en",    
            "operator",
            "lng_cng",            
            ]



class GasFillingStationSerializer(GeoFeatureModelSerializer):
    gas_filling_station_content = GasFillingStationContentSerializer(many=False, read_only=True)
    class Meta:
        model = MobileUnit
        geo_field = "geometry"
        fields = [
            "geometry",
            "gas_filling_station_content",
        ]


   