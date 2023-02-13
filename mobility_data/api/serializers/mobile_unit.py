from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import (
    GEOSGeometry,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)
from rest_framework import serializers

from services.models import Unit

from ...models import GroupType, MobileUnit, MobileUnitGroup
from . import ContentTypeSerializer
from .utils import swap_coords


class GeometrySerializer(serializers.Serializer):

    x = serializers.FloatField()
    y = serializers.FloatField()

    class Meta:
        fields = "__all__"


class GrouptTypeBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupType
        fields = ["id", "name"]


class MobileUnitGroupBasicInfoSerializer(serializers.ModelSerializer):

    group_type = GrouptTypeBasicInfoSerializer(many=False, read_only=True)

    class Meta:
        model = MobileUnitGroup
        fields = ["id", "name", "group_type"]


class MobileUnitSerializer(serializers.ModelSerializer):

    content_types = ContentTypeSerializer(many=True, read_only=True)
    mobile_unit_group = MobileUnitGroupBasicInfoSerializer(many=False, read_only=True)
    geometry_coords = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MobileUnit
        fields = [
            "id",
            "name",
            "name_fi",
            "name_sv",
            "name_en",
            "address",
            "address_fi",
            "address_sv",
            "address_en",
            "address_zip",
            "municipality",
            "description",
            "description_fi",
            "description_sv",
            "description_en",
            "content_types",
            "mobile_unit_group",
            "is_active",
            "created_time",
            "geometry",
            "geometry_coords",
            "extra",
            "unit_id",
        ]

    # Contains the corresponding field names of the MobileUnit model if they differs
    # from the Unit model.
    mobile_unit_to_unit_field_mappings = {
        "address": "street_address",
        "address_fi": "street_address_fi",
        "address_sv": "street_address_sv",
        "address_en": "street_address_en",
    }

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        # If mobile_unit has a unit_id we serialize the data from the services_unit table.
        unit_id = obj.unit_id
        if unit_id:
            unit = Unit.objects.get(id=unit_id)
            for field in self.fields:
                # lookup the field name in the service_unit table, as not all field names that contains
                # similar data has the same name.
                if field in self.mobile_unit_to_unit_field_mappings:
                    key = self.mobile_unit_to_unit_field_mappings[field]
                else:
                    key = field

                if hasattr(unit, key):
                    # unit.municipality is of type munigeo.models.Municipality and not serializable
                    if key == "municipality":
                        representation[field] = unit.municipality.id
                    else:
                        representation[field] = getattr(unit, key)
                # Serialize the MobileUnit id, otherwise would serialize the serivce_unit id.
                if field == "id":
                    representation["id"] = obj.id
            # The location field must be serialized with its wkt value.
            if unit.location:
                representation["geometry"] = unit.location.wkt
        return representation

    def get_geometry_coords(self, obj):
        # If stored to Unit table, retrieve geometry from there.
        if obj.unit_id:
            geometry = Unit.objects.get(id=obj.unit_id).location
        else:
            geometry = obj.geometry
        if isinstance(geometry, GEOSGeometry):
            srid = self.context["srid"]
            if srid:
                try:
                    geometry.transform(srid)
                except GDALException:
                    return "Invalid SRID given as parameter for transformation."
        if isinstance(geometry, Point):
            pos = {}
            if self.context["latlon"] is True:
                pos["lat"] = geometry.y
                pos["lon"] = geometry.x
            else:
                pos["lon"] = geometry.x
                pos["lat"] = geometry.y
            return pos
        elif isinstance(geometry, LineString):
            if self.context["latlon"]:
                # Return LineString coordinates in (lat,lon) format
                coords = []
                for coord in geometry.coords:
                    # swap lon,lat -> lat lon
                    e = swap_coords(coord)
                    coords.append(e)
                return coords
            else:
                return geometry.coords
        elif isinstance(geometry, Polygon):
            if self.context["latlon"]:
                # Return Polygon coordinates in (lat,lon) format
                # The polygon needs to be a three dimensional array
                # to be compatible with Leaflet polygon element.
                polygon = []
                coords = []
                # If geometry.coords contains multiple lists they must be handled separately.
                if len(geometry.coords) > 1:
                    for geometry_coords in geometry.coords:
                        for coord in geometry_coords:
                            # swap lon,lat -> lat lon
                            coords.append(swap_coords(coord))
                else:
                    for coord in list(*geometry.coords):
                        coords.append(swap_coords(coord))
                polygon.append(coords)
                return polygon
            else:
                return geometry.coords
        elif isinstance(geometry, MultiPolygon):
            if self.context["latlon"]:
                coords = []
                # Iterate through all the polygons in the multipolygon
                # Create a list of swapped coords for every polygon
                for polygon in geometry.coords:
                    polygon_coords = []
                    for p_c in list(*polygon):
                        # swap lon,lat -> lat lon
                        polygon_coords.append(swap_coords(p_c))
                    coords.append(polygon_coords)
                return coords
            else:
                return geometry.coords
        elif isinstance(geometry, MultiLineString):
            if self.context["latlon"]:
                coords = []
                for linestring in geometry.coords:
                    linestring_coords = []
                    # swap lon,lat -> lat lon
                    for coord in linestring:
                        linestring_coords.append(swap_coords(coord))
                    coords.append(linestring_coords)
                return coords
            else:
                return geometry.coords
        else:
            return ""
