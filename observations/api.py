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
            properties = self.get_observable_properties(obj)
            observations = []
            for prop in properties:
                observations.append(obj.observations.filter(property=prop).order_by('-time').first())
            data['observations'] = [
                ObservationSerializer(observation).data
                for observation in observations if observation]
        return data

class ObservableServiceSerializer(ObservableSerializerMixin, ServiceSerializer):
    def get_observable_properties(self, service):
        return service.observable_properties.all()

class ObservableUnitSerializer(ObservableSerializerMixin, UnitSerializer):
    def get_observable_properties(self, unit):
        return models.ObservableProperty.objects.filter(services__in=unit.services.all())

UnitViewSet.serializer_class = ObservableUnitSerializer
ServiceViewSet.serializer_class = ObservableServiceSerializer

views = [
    {'class': ObservationViewSet, 'name': 'observation' }
]
