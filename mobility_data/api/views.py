import sys
from django.conf import settings
from django.contrib.gis.gdal.error import GDALException
from rest_framework import status, viewsets
from rest_framework.response import Response
from .utils import transform_queryset, transform_group_queryset
from ..models import (
    MobileUnitGroup,
    MobileUnit,
    ContentType,
    GroupType,
    GasFillingStationContent,
    ChargingStationContent,
)
from .serializers import(   
    MobileUnitGroupSerializer, 
    MobileUnitSerializer,   
    GroupTypeSerializer,
    ContentTypeSerializer,
    ChargingStationContentSerializer,
    ChargingStationSerializer,
    GasFillingStationContentSerializer,
    GasFillingStationSerializer,
)

class MobileUnitGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MobileUnitGroup.objects.all()
    serializer_class = MobileUnitGroupSerializer

    def retrieve(self, request, pk=None):
        pass
        srid = request.query_params.get("srid", None)


    def list(self, request):
        type_name = request.query_params.get("type_name", None)        
        srid = request.query_params.get("srid", None)
        queryset = None
        if not type_name:
            queryset = MobileUnitGroup.objects.all()
        else:
            if not GroupType.objects.filter(type_name=type_name).exists():
                return Response("type_name does not exist.", status=status.HTTP_400_BAD_REQUEST)

            queryset = MobileUnitGroup.objects.filter(group_type__type_name=type_name)
     
        # if srid: 
        #     #success, queryset = transform_group_queryset(srid, queryset)
        #     trans_qs = MobileUnitGroup.objects.none()
        #     ids = []
            # for i,elem in enumerate(queryset):
            #     # qs returns OK tranformed coords
            #     success, qs = transform_queryset(srid, elem.units.all())
            #     queryset[i].units.set(qs) # EI VITTU TEE MITÄÄN
            # for i,elem in enumerate(queryset):
            #     for j, unit in enumerate(elem.units.all()):
            #         setattr(queryset[i].units.all()[j],"geometry", unit.geometry.transform(srid))    
            
            # for elem in queryset:
            #     for unit in elem.units.all():

            #         unit.transform()
            # # if not success:
            #     return Response("Invalid SRID.", status=status.HTTP_400_BAD_REQUEST)
    
        page = self.paginate_queryset(queryset)
        serializer = MobileUnitGroupSerializer(queryset, many=True)
        if srid:
            for i, elem in enumerate(serializer.data):
                geom = elem["unit"]["features"][0]["geometry"]
                GeomClass = getattr(sys.modules["django.contrib.gis.geos"], geom["type"])
                geom_obj = GeomClass()
                geom_obj = GeomClass(geom["coordinates"], srid=settings.DEFAULT_SRID)
                geom_obj.transform(srid)
                geom["coordinates"] = geom_obj.coords
                serializer.data[i]["unit"]["features"][0] = geom
         
     
        response = self.get_paginated_response(serializer.data)           
        return Response(response.data, status=status.HTTP_200_OK)
     


    

class MobileUnitViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = MobileUnit.objects.all()
    serializer_class = MobileUnitSerializer     
        
    def retrieve(self, request, pk=None):
        unit = MobileUnit.objects.get(pk=pk)
        srid = request.query_params.get("srid", None)
        if srid:
            try:
                unit.geometry.transform(srid)
            except GDALException:
                return Response("Invalid SRID.", status=status.HTTP_400_BAD_REQUEST)
        serializer = MobileUnitSerializer(unit, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def list(self, request):
        type_name = request.query_params.get("type_name", None)        
        srid = request.query_params.get("srid", None)
        queryset = None
        serializer = None 
        if not type_name:
            queryset = MobileUnit.objects.all()
            if srid:
                success, queryset = transform_queryset(srid, queryset)
                if not success:
                    return Response("Invalid SRID.", status=status.HTTP_400_BAD_REQUEST)

            page = self.paginate_queryset(queryset)
            serializer = MobileUnitSerializer(queryset, many=True)
        else:
            if not ContentType.objects.filter(type_name=type_name).exists():
                return Response("type_name does not exist.", status=status.HTTP_400_BAD_REQUEST)

            queryset = MobileUnit.objects.filter(content_type__type_name=type_name)
            if srid:
                success, queryset = transform_queryset(srid, queryset)
                if not success:
                    return Response("Invalid SRID.", status=status.HTTP_400_BAD_REQUEST)
            page = self.paginate_queryset(queryset)
            class_name = ContentType.objects.get(type_name=type_name).class_name
            serializer_class = getattr(sys.modules[__name__], class_name+"Serializer")
            serializer = serializer_class(queryset, many=True)
        
        response = self.get_paginated_response(serializer.data)
        return Response(response.data, status=status.HTTP_200_OK)


# class GeometryViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Geometry.objects.all()
#     serializer_class = GeometrySerializer


class GroupTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer
   
        #wueryset = MobileUnitGroup.objects.filter

class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer


class ChargingStationContentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChargingStationContent.objects.all()
    serializer_class = ChargingStationContentSerializer


class GasFillingStationtContentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GasFillingStationContent.objects.all()
    serializer_class = GasFillingStationContentSerializer