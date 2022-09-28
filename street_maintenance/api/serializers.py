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
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceWork
        fields = [
            "id",
            "maintenance_unit",
            "point",
            "timestamp",
            "events",
            "lat",
            "lon",
        ]

    def get_lat(self, obj):
        return obj.point.y

    def get_lon(self, obj):
        return obj.point.x
