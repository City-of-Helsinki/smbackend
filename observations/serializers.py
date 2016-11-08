from services.api import (
    ServiceSerializer, UnitSerializer,
    TranslatedModelSerializer)

from django.apps import apps
from rest_framework import serializers
from django.utils import timezone

from . import models
from services.api import JSONAPISerializer

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

class ObservationSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        observable_property = obj.property
        allowed_value = obj.property.allowed_values.get(internal_value=obj.value)
        name = allowed_value.name
        description = allowed_value.description
        return dict(
            unit=int(obj.unit_id),
            id=obj.id,
            property=observable_property.id,
            time=timezone.localtime(obj.time).strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
            value=observable_property.get_external_value(obj.value),
            quality=allowed_value.quality,
            name=name,
        )
    def to_internal_value(self, data):
        if 'time' in data:
            raise ValidationError(
                'The observation time cannot be explicitly set. '
                'It is always the current time.')
        return dict(
            unit_id=data['unit'],
            property_id=data['property'],
            time=timezone.now(),
            value=data['value']
        )
    def create(self, validated_data):
        property = validated_data['property_id']
        observable_property = models.ObservableProperty.objects.get(id=property)
        validated_data['value'] = observable_property.get_internal_value(
            validated_data['value'])
        observation_type = observable_property.observation_type
        ModelClass = apps.get_model(observation_type)
        return ModelClass.objects.create(**validated_data)
