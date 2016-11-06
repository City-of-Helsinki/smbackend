from rest_framework import serializers, viewsets
from . import models
from .serializers import ObservationSerializer

from django.apps import apps

from services.api import (
    JSONAPIViewSetMixin, ServiceSerializer, UnitSerializer,
    ServiceViewSet, UnitViewSet, TranslatedModelSerializer)

class ObservationViewSet(JSONAPIViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Observation.objects.all()
    serializer_class = ObservationSerializer

class AllowedValueSerializer(TranslatedModelSerializer):
    class Meta:
        model = models.AllowedValue
        exclude = ('id', 'internal_value', 'property')

class ObservablePropertySerializer(TranslatedModelSerializer):
    allowed_values = AllowedValueSerializer(many=True, read_only=True)
    class Meta:
        model = models.ObservableProperty
    def to_representation(self, obj):
        data = super(ObservablePropertySerializer, self).to_representation(obj)
        ModelClass = apps.get_model(obj.observation_type)
        data['observation_type'] = ModelClass.get_type()
        return data
        

class ObservableSerializerMixin:
    def to_representation(self, obj):
        data = super(ObservableSerializerMixin, self).to_representation(obj)
        if 'observable_properties' not in self.context.get('include', []):
            return data

        data['observable_properties'] = ObservablePropertySerializer(
            self.get_observable_properties(obj), many=True).data
        return data

class ObservableServiceSerializer(ObservableSerializerMixin, ServiceSerializer):
    def get_observable_properties(self, service):
        return service.observable_properties.all()

class ObservableUnitSerializer(ObservableSerializerMixin, UnitSerializer):
    def get_observable_properties(self, unit):
        services = unit.services.all()
        return models.ObservableProperty.objects.filter(services__in=services)

UnitViewSet.serializer_class = ObservableUnitSerializer
ServiceViewSet.serializer_class = ObservableServiceSerializer

views = [
    {'class': ObservationViewSet, 'name': 'observation' }
]
