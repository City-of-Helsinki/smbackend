from django.contrib.gis.geos import LineString, Point
from rest_framework import serializers

from street_maintenance.models import MaintenanceUnit, MaintenanceWork


class HistoryGeometrySerializer(serializers.Serializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["geometry"] = obj
        return representation


class ActiveEventSerializer(serializers.Serializer):
    events = serializers.CharField(max_length=64)


class MaintenanceUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceUnit
        fields = "__all__"


class MaintenanceWorkSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(
        many=False, source="maintenance_unit.provider", read_only=True
    )

    class Meta:
        model = MaintenanceWork
        fields = [
            "id",
            "maintenance_unit",
            "provider",
            "geometry",
            "timestamp",
            "events",
        ]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        if isinstance(obj.geometry, Point):
            representation["lat"] = obj.geometry.y
            representation["lon"] = obj.geometry.x
        elif isinstance(obj.geometry, LineString):
            representation["coords"] = obj.geometry.coords
        return representation
