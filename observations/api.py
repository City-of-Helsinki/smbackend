from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from services.api import (
    JSONAPIViewSetMixin,
    ServiceSerializer,
    ServiceViewSet,
    UnitSerializer,
    UnitViewSet,
)

from . import models
from .serializers import ObservablePropertySerializer, ObservationSerializer


class ObservationViewSet(JSONAPIViewSetMixin, viewsets.ModelViewSet):
    queryset = models.Observation.objects.all()
    serializer_class = ObservationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        if request.auth is None:
            raise AuthenticationFailed(_('Authentication required.'))

        return super(ObservationViewSet, self).create(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'user': self.request.user, 'auth': self.request.auth})
        return context


class ObservableSerializerMixin:
    def to_representation(self, obj):
        data = super(ObservableSerializerMixin, self).to_representation(obj)
        if 'observable_properties' in self.context.get('include', []):
            data['observable_properties'] = ObservablePropertySerializer(
                self.get_observable_properties(obj), many=True).data
        if 'observations' in self.context.get('include', []):
            observations = self.get_observations(obj)
            if observations:
                data['observations'] = ObservationSerializer(
                    observations, many=True).data

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
    {'class': ObservationViewSet, 'name': 'observation'}
]
