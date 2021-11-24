from rest_framework import serializers
from ..models import (
    BicycleNetwork,
    BicycleNetworkPart,
)

class BicycleNetworkSerializer(serializers.ModelSerializer):

    class Meta:
        model = BicycleNetwork
        fields = "__all__"


class BicycleNetworkPartCoordsSerializer(serializers.ModelSerializer):
    
    geometry_coords = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = BicycleNetworkPart
        fields = ["id", "geometry_coords"]


    def get_geometry_coords(self, obj):
        if obj.geometry:
            if self.context["lonlat"]:
                return obj.geometry.coords
            else:
                # Return linestring coordinates in (lat,lon) format
                coords = []
                for coord in obj.geometry.coords:
                    # swap lon,lat -> lat lon
                    e=(coord[1],coord[0])
                    coords.append(e)                
                return coords
        else:
            return None


class BicycleNetworkPartSerializer(BicycleNetworkPartCoordsSerializer):

    bicycle_network_name = serializers.CharField(read_only=True, source="bicycle_network.name")
  
    class Meta:
        model = BicycleNetworkPart
        fields = [
            "geometry",
            "toiminnall",
            "liikennevi",
            "teksti",
            "tienim2",
            "TKU_toiminnall_pp",
            "bicycle_network_name",
            "geometry_coords"            
        ]

 