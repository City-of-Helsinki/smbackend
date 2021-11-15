from mobility_data.api.serializers.mobile_unit import MobileUnitSerializer
from rest_framework import serializers
from . import MobileUnitSerializer
from ...models import  MobileUnitGroup, MobileUnit

class MobileUnitGroupBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUnitGroup
        fields = [
            "id",
            "name",
            "name_fi",
            "name_sv",
            "name_en",            
            "description",
            "description_fi",
            "description_sv",            
            "description_en",
        ]  

class MobileUnitGroupSerializer(MobileUnitGroupBaseSerializer):
  
    mobile_units = serializers.SerializerMethodField()
    class Meta:
        model = MobileUnitGroup
        fields = [            
            "mobile_units"
        ]

    def get_mobile_units(self, obj):
        qs = MobileUnit.objects.filter(mobile_unit_group=obj)
        serializer = MobileUnitSerializer(qs, many=True,\
            read_only=True, context=self.context)
        return serializer.data