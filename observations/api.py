from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from . import models
from .serializers import *

from django.contrib.contenttypes.models import ContentType


from services.api import (
    JSONAPIViewSetMixin, ServiceViewSet, UnitViewSet)

class ObservationViewSet(JSONAPIViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Observation.objects.all()
    serializer_class = ObservationSerializer

class ObservableSerializerMixin:
    def to_representation(self, obj):
        data = super(ObservableSerializerMixin, self).to_representation(obj)
        if 'observable_properties' in self.context.get('include', []):
            data['observable_properties'] = ObservablePropertySerializer(
                self.get_observable_properties(obj), many=True).data
        if 'observations' in self.context.get('include', []):
            observations = self.get_observations(obj)
            if observations:
                data['observations'] = ObservationSerializer(observations, many=True).data
        return data

class ObservableServiceSerializer(ObservableSerializerMixin, ServiceSerializer):
    def get_observable_properties(self, service):
        return service.observable_properties.all()
    def get_observations(self, service):
        return None

class ObservableUnitSerializer(ObservableSerializerMixin, UnitSerializer):
    def get_observable_properties(self, unit):
        return models.ObservableProperty.objects.filter(services__in=unit.services.all())
    def get_observations(self, unit):
        return unit.observation_set

UnitViewSet.serializer_class = ObservableUnitSerializer
ServiceViewSet.serializer_class = ObservableServiceSerializer

views = [
    {'class': ObservationViewSet, 'name': 'observation' }
]
