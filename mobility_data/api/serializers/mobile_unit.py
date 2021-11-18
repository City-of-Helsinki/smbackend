from django.contrib.gis.gdal.error import GDALException
from django.core import serializers 
from django.contrib.gis.geos import GEOSGeometry, Point, LineString
from rest_framework import serializers
from . import  ContentTypeSerializer
from ...models import MobileUnit, MobileUnitGroup, GroupType


class GeometrySerializer(serializers.Serializer):
    
    x = serializers.FloatField()
    y = serializers.FloatField()    
    class Meta:
        fields = "__all__"


class GrouptTypeBasicInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupType
        fields = ["id", "name", "type_name"]


class MobileUnitGroupBasicInfoSerializer(serializers.ModelSerializer):

    group_type = GrouptTypeBasicInfoSerializer(
        many=False, 
        read_only=True        
    )
    class Meta:
        model = MobileUnitGroup
        fields = ["id", "name", "group_type"]


class MobileUnitSerializer(serializers.ModelSerializer):

    content_type = ContentTypeSerializer(
        many=False, 
        read_only=True        
    )
    mobile_unit_group = MobileUnitGroupBasicInfoSerializer(
        many=False,
        read_only=True
    )
    geometry_data = serializers.SerializerMethodField(read_only=True)
    
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
            "mobile_unit_group",
            "is_active",
            "created_time",
            "geometry",
            "geometry_data",
            "extra",          
        ]

    def get_geometry_data(self, obj):
        if isinstance(obj.geometry, GEOSGeometry):
            srid = self.context["srid"]
            if srid:
                try:
                    obj.geometry.transform(srid)
                except GDALException:
                    return "Invalid SRID given as parameter for transformation." 
        if isinstance(obj.geometry, Point):           
            pos = {}
            pos["x"] = obj.geometry.x
            pos["y"] = obj.geometry.y
            return pos
        elif isinstance(obj.geometry, LineString):
            return obj.geometry.coords          
        else:
            return ""

