from mobility_data.api.serializers.mobile_unit import MobileUnitSerializer
from rest_framework import serializers
from . import MobileUnitSerializer
from ...models import  MobileUnitGroup


class MobileUnitGroupSerializer(serializers.ModelSerializer):
    mobile_units = MobileUnitSerializer(
        many=True,
        read_only=True,      
    )

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
            "mobile_units"
        ]