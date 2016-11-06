from rest_framework import serializers

from . import models
from services.api import JSONAPISerializer

class ObservationSerializer(JSONAPISerializer):
    class Meta:
        model = models.Observation

# class ObservablePropertySerializer(JSONAPISerializer):
#     class Meta:
#         model = ObservableProperty
