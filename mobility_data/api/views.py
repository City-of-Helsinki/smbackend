import sys
from django.conf import settings
from django.contrib.gis.gdal.error import GDALException
from rest_framework import status, viewsets
from rest_framework.response import Response
from .utils import transform_queryset
from ..models import (
    MobileUnitGroup,
    MobileUnit,
    ContentType,
    GroupType,   
)
from .serializers import(   
    MobileUnitGroupSerializer, 
    MobileUnitSerializer,   
    GroupTypeSerializer,
    ContentTypeSerializer,    
)


class MobileUnitGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MobileUnitGroup.objects.all()
    serializer_class = MobileUnitGroupSerializer
    # TODO, when real data becames available implement custom methods as needed.
    

class MobileUnitViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = MobileUnit.objects.all()
    serializer_class = MobileUnitSerializer     
        
    def retrieve(self, request, pk=None):
        try:
            unit = MobileUnit.objects.get(pk=pk)
        except MobileUnit.DoesNotExist:
            return Response("Mobile unit does not exist", status=status.HTTP_400_BAD_REQUEST)
        srid = request.query_params.get("srid", None)
        if srid:
            try:
                unit.geometry.transform(srid)
            except GDALException:
                return Response("Invalid SRID.", status=status.HTTP_400_BAD_REQUEST)
        serializer = MobileUnitSerializer(unit, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def list(self, request):
        """
        Lists MobileUnits, optionally list by type_name if given
        and transforms to given srid.
        """
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
           
            serializer = MobileUnitSerializer(queryset, many=True)
        
        response = self.get_paginated_response(serializer.data)
        return Response(response.data, status=status.HTTP_200_OK)


class GroupTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer
  

class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer


