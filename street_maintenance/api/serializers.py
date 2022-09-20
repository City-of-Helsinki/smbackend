from rest_framework import serializers

from street_maintenance.models import MaintenanceUnit, MaintenanceWork


class ActiveEventSerializer(serializers.Serializer):
    events = serializers.CharField(max_length=64)


class MaintenanceUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceUnit
        fields = "__all__"


class MaintenanceWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceWork
        fields = "__all__"
