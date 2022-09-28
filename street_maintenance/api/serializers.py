from rest_framework import serializers

from street_maintenance.models import MaintenanceUnit, MaintenanceWork


class HistoryGeometrySerializer(serializers.Serializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["event"] = obj["event"]
        if "linestrings" in obj:
            for i, linestring in enumerate(obj["linestrings"]):
                field_name = f"linestring_{i}"
                representation[field_name] = list(linestring)
        if "points" in obj:
            for i, point in enumerate(obj["points"]):
                field_name = f"point_{i}"
                representation[field_name] = list(point)
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
