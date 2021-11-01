import json
from django.core import serializers as django_serializers
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .content_type import ContentTypeSerializer
from ...models import(
    MobileUnit,
    ContentType,   
)


class UnitInfoSerializer(serializers.ModelSerializer):
  
    class Meta:
        model = MobileUnit
        fields = [
            "id",
            "created_time",
            "is_active",
        ]    


class MobileUnitSerializer(GeoFeatureModelSerializer):
    content_type = ContentTypeSerializer(
        many=False, 
        read_only=True        
    )
    content = serializers.SerializerMethodField()

    class Meta:
        model = MobileUnit
        geo_field = "geometry"
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
            "is_active",
            "created_time",
            "geometry",
            "content_type",
            "content"
        ]
    def get_content(self, obj):
        content = None        
        if obj.content_type.type_name == ContentType.GAS_FILLING_STATION:
            content = obj.gas_filling_station_content           
        elif obj.content_type.type_name == ContentType.CHARGING_STATION:
            content = obj.charging_station_content 
        elif obj.content_type.type_name == ContentType.STATUE:
            content = obj.statue_content
        elif obj.content_type.type_name == ContentType.WALKING_ROUTE:
            content = obj.walking_route_content      
        else:
            return ""
        ser_data = django_serializers.serialize("json",[content,])
        return json.loads(ser_data) 


# class UnitSerializer(OLDGeoFeatureModelSerializer):
#     = UnitInfoSerializer()
#     content_type = ContentTypeSerializer(
#         many=False, 
#         read_only=True, 
#         source="content_type"
#     )
#     content = serializers.SerializerMethodField()
#     class Meta: 
#         model = Geometry
#         geo_field = "geometry"
#         fields = [
#             "id",
#             "geometry",
#             "content_type",
#             ",
#             "content"
#         ]

#     def get_content(self, obj):
#         content = None
#         if obj.content_type.type_name == ContentTypes.GAS_FILLING_STATION:
#             content = obj.gas_filling_station_content           
#         elif obj.content_type.type_name == ContentTypes.CHARGING_STATION:
#             content = obj.charging_station_content 
#         elif obj.content_type.type_name == ContentTypes.STATUE:
#             content = obj.statue_content
#         elif obj.content_type.type_name == ContentTypes.WALKING_ROUTE:
#             content = obj.walking_route_content      
#         else:
#             return ""
#         ser_data = django_serializers.serialize("json",[content,])
#         return json.loads(ser_data) 
