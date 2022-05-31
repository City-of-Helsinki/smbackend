from django.contrib.gis.geos import LineString, MultiLineString
from rest_framework import serializers

from ..models import BicycleNetwork, BicycleNetworkPart


class BicycleNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BicycleNetwork
        fields = ["id", "name_fi", "name_sv", "name_en", "length"]


class BicycleNetworkPartCoordsSerializer(serializers.ModelSerializer):

    geometry_coords = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BicycleNetworkPart
        fields = ["id", "geometry_coords"]

    def get_geometry_coords(self, obj):
        if obj.geometry:
            if self.context["latlon"] is True:
                if isinstance(obj.geometry, LineString):
                    # Return LineString coordinates in (lat,lon) format
                    coords = []
                    for coord in obj.geometry.coords:
                        # swap lon,lat -> lat lon
                        e = (coord[1], coord[0])
                        coords.append(e)
                    return coords
                elif isinstance(obj.geometry, MultiLineString):
                    coords = []
                    for linestring in obj.geometry.coords:
                        # swap lon,lat -> lat lon
                        for coord in linestring:
                            e = (coord[1], coord[0])
                            coords.append(e)
                    return coords
            else:
                return obj.geometry.coords

        else:
            return None


class BicycleNetworkPartSerializer(BicycleNetworkPartCoordsSerializer):

    bicycle_network_name = serializers.CharField(
        read_only=True, source="bicycle_network.name"
    )

    class Meta:
        model = BicycleNetworkPart
        fields = ["id", "bicycle_network_name", "geometry", "geometry_coords"]
