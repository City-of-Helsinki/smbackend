from rest_framework import serializers

from ...models import MobileUnit, MobileUnitGroup
from . import GroupTypeSerializer, MobileUnitSerializer

FIELDS = [
    "id",
    "name",
    "group_type",
    "name_fi",
    "name_sv",
    "name_en",
    "description",
    "description_fi",
    "description_sv",
    "description_en",
]


class MobileUnitGroupSerializer(serializers.ModelSerializer):
    group_type = GroupTypeSerializer(many=False, read_only=True)

    class Meta:
        model = MobileUnitGroup
        fields = FIELDS


class MobileUnitGroupUnitsSerializer(serializers.ModelSerializer):
    group_type = GroupTypeSerializer(many=False, read_only=True)
    mobile_units = serializers.SerializerMethodField()

    class Meta:
        model = MobileUnitGroup
        fields = FIELDS + ["mobile_units"]

    def get_mobile_units(self, obj):
        """
        Returns all the MobileUnits that are in the MobileUnitGroup.
        """
        qs = MobileUnit.objects.filter(mobile_unit_group=obj)
        serializer = MobileUnitSerializer(
            qs, many=True, read_only=True, context=self.context
        )
        return serializer.data
