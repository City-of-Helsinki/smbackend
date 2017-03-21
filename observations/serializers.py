from collections import OrderedDict
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError

from services.api import TranslatedModelSerializer
from . import models

class AllowedValueSerializer(TranslatedModelSerializer, serializers.Serializer):
    identifier = serializers.CharField(required=False)
    quality = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_null=True)
    class Meta:
        model = models.AllowedValue

class ObservablePropertySerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    allowed_values = AllowedValueSerializer(many=True, read_only=True)
    class Meta:
        model = models.ObservableProperty
    def to_representation(self, obj):
        data = super(ObservablePropertySerializer, self).to_representation(obj)
        data['observation_type'] = obj.get_observation_type()
        return data


class BaseObservationSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        return dict(
            unit=int(obj.unit_id),
            id=obj.id,
            property=obj.property_id,
            time=timezone.localtime(obj.time).strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
        )
    def to_internal_value(self, data):
        return dict(
            auth=self.context['auth'],
            unit_id=data['unit'],
            property_id=data['property'],
            time=timezone.now(),
            value=data['value'],
            add_maintenance_observation=data.get('serviced', False))


class DescriptiveObservationSerializer(BaseObservationSerializer):
    def __init__(self, *args, **kwargs):
        super(DescriptiveObservationSerializer, self).__init__(*args, **kwargs)
    def to_internal_value(self, data):
        result = super(DescriptiveObservationSerializer, self).to_internal_value(data)
        val = result['value']
        if val is None:
            return result
        default_language = settings.LANGUAGES[0][0]
        if type(val) == str:
            val = {default_language: val}
        serializer = AllowedValueSerializer(
            data={'description': val, 'property_id': result['property_id']})
        serializer.is_valid(raise_exception=True)
        result['value'] = serializer.validated_data
        return result
    def to_representation(self, obj):
        result = super(DescriptiveObservationSerializer, self).to_representation(obj)
        val = obj.get_external_value()
        serialized_allowed_value = AllowedValueSerializer(val, read_only=True).data
        result.update({'value': serialized_allowed_value['description']})
        return result
    class Meta:
        model = models.DescriptiveObservation

class CategoricalObservationSerializer(BaseObservationSerializer):
    def to_representation(self, obj):
        result = super(CategoricalObservationSerializer, self).to_representation(obj)
        allowed_value = obj.value
        if allowed_value is None:
            result.update({'value': None})
            return result
        else:
            serialized_allowed_value = AllowedValueSerializer(allowed_value, read_only=True).data
        result.update({
            'name': serialized_allowed_value['name'],
            'quality': allowed_value.quality,
            'value': obj.get_external_value()
        })
        return result
    class Meta:
        model = models.CategoricalObservation


def get_serializer_by_class(cls):
    if cls == models.CategoricalObservation:
        return CategoricalObservationSerializer
    elif cls == models.DescriptiveObservation:
        return DescriptiveObservationSerializer

def get_serializer_by_object(obj):
    if isinstance(obj, models.CategoricalObservation):
        return CategoricalObservationSerializer
    elif isinstance(obj, models.DescriptiveObservation):
        return DescriptiveObservationSerializer

class ObservationSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        observable_property = obj.property
        serializer = get_serializer_by_object(obj)
        return serializer(obj, context=self.context).to_representation(obj)

    def to_internal_value(self, data):
        if 'time' in data:
            raise ValidationError(
                'The observation time cannot be explicitly set. '
                'It is always the current time.')
        observable_property = models.ObservableProperty.objects.get(pk=data['property'])
        model = observable_property.get_observation_model()
        serializer = get_serializer_by_class(model)
        return serializer(data=data, context=self.context).to_internal_value(data)

    def create(self, validated_data):
        property = validated_data['property_id']
        observable_property = models.ObservableProperty.objects.get(id=property)
        has_value = 'value' in validated_data and validated_data['value'] is not None
        if has_value:
            validated_data['value'] = observable_property.get_internal_value(validated_data['value'])
        with transaction.atomic():
            if has_value:
                if (validated_data['add_maintenance_observation']):
                    # TODO: refactor below
                    if validated_data['property_id'] == 'ski_trail_condition':
                        observable_property = models.ObservableProperty.objects.get(id='ski_trail_maintenance')
                        MaintenanceModelClass = apps.get_model(observable_property.observation_type)
                        obj = MaintenanceModelClass.objects.create(
                            unit_id=validated_data['unit_id'],
                            property_id='ski_trail_maintenance',
                            time=validated_data['time'],
                            auth=validated_data['auth'],
                            value=observable_property.get_internal_value('maintenance_finished'))
                        models.UnitLatestObservation.objects.update_or_create(
                            unit_id=validated_data['unit_id'],
                            property_id='ski_trail_maintenance',
                            defaults={'observation_id': obj.pk})
            del validated_data['add_maintenance_observation']
            obj = observable_property.create_observation(**validated_data)
            if 'value' in validated_data and validated_data['value'] is None:
                # POSTing a null value removes the property
                # from the unit's latest observations
                try:
                    ulo = models.UnitLatestObservation.objects.get(
                        unit_id=validated_data['unit_id'],
                        property_id=validated_data['property_id'])
                    ulo.delete()
                except models.UnitLatestObservation.DoesNotExist:
                    pass
            else:
                models.UnitLatestObservation.objects.update_or_create(
                    unit_id=validated_data['unit_id'],
                    property_id=validated_data['property_id'],
                    defaults={'observation_id': obj.pk})
            return obj
