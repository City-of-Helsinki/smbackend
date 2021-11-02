import json
from django.core import serializers as django_serializers
from rest_framework import serializers
from .content_type import ContentTypeSerializer
from ...models import MobileUnit


class GeometrySerializer(serializers.Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()    
    class Meta:
        fields = "__all__"


class MobileUnitSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(
        many=False, 
        read_only=True        
    )
    geometry_data = GeometrySerializer(source="geometry")

    class Meta:
        model = MobileUnit
        fields =  [
            "id",
            "name",
            "name_fi",
            "name_sv",
            "name_en",  
            "address",
            "address_fi",
            "address_sv",
            "address_en",
            "description",
            "description_fi",
            "description_sv",
            "description_en",
            "content_type",
            "is_active",
            "created_time",
            "geometry_data",
            "extra",          
        ]
   
