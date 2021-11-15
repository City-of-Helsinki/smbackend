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
    MobileUnitGroupBaseSerializer,
    MobileUnitSerializer,   
    GroupTypeSerializer,
    ContentTypeSerializer,    
)


class MobileUnitGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MobileUnitGroup.objects.all()
    serializer_class = MobileUnitGroupSerializer
    
    def retrieve(self, request, pk=None):
        try:
            unit = MobileUnitGroup.objects.get(pk=pk)
        except MobileUnitGroup.DoesNotExist:
            return Response("Mobile unit group does not exist", status=status.HTTP_400_BAD_REQUEST)
        srid = request.query_params.get("srid", None)
        serializer = MobileUnitGroupSerializer(unit, many=False, context={"srid":srid})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        type_name = request.query_params.get("type_name", None)        
        srid = request.query_params.get("srid", None)
        show_mobile_units = request.query_params.get("show_mobile_units", False)
        queryset = None
        serializer = None 

        if type_name:
            if not GroupType.objects.filter(type_name=type_name).exists():
                return Response("type_name does not exist.", status=status.HTTP_400_BAD_REQUEST)
            queryset = MobileUnitGroup.objects.filter(group_type__type_name=type_name)         
        else:
            queryset = MobileUnitGroup.objects.all()           

        page = self.paginate_queryset(queryset)
        serializer_class = None
        if show_mobile_units:
            serializer_class = MobileUnitGroupSerializer
        else:
            serializer_class = MobileUnitGroupBaseSerializer


        serializer = serializer_class(page, many=True, context={"srid":srid})
        return Response(serializer.data, status=status.HTTP_200_OK)

class MobileUnitViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = MobileUnit.objects.all()
    serializer_class = MobileUnitSerializer     
        
    def retrieve(self, request, pk=None):
        try:
            unit = MobileUnit.objects.get(pk=pk)
        except MobileUnit.DoesNotExist:
            return Response("Mobile unit does not exist", status=status.HTTP_400_BAD_REQUEST)
        srid = request.query_params.get("srid", None)
        serializer = MobileUnitSerializer(unit, many=False, context={"srid":srid})
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
        if type_name:
            if not ContentType.objects.filter(type_name=type_name).exists():
                return Response("type_name does not exist.", status=status.HTTP_400_BAD_REQUEST)
            queryset = MobileUnit.objects.filter(content_type__type_name=type_name)          
        else:
            queryset = MobileUnit.objects.all()       
        
        page = self.paginate_queryset(queryset)
        serializer = MobileUnitSerializer(page, many=True, context={"srid": srid})    
        return Response(serializer.data, status=status.HTTP_200_OK)


class GroupTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer
  

class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer


