from rest_framework import status, viewsets
from rest_framework.response import Response
from ..models import (
    MobileUnitGroup,
    MobileUnit,
    ContentType,
    GroupType,   
)
from .serializers import(   
    MobileUnitGroupSerializer, 
    MobileUnitGroupUnitsSerializer,
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
            return Response("MobileUnitGroup does not exist.", status=status.HTTP_400_BAD_REQUEST)
        srid = request.query_params.get("srid", None)
        mobile_units = request.query_params.get("mobile_units", False)
        serializer_class = None
        if mobile_units:
            serializer_class = MobileUnitGroupUnitsSerializer
        else:
            serializer_class = MobileUnitGroupSerializer

        serializer = serializer_class(unit, many=False, context={"srid":srid})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        type_name = request.query_params.get("type_name", None)        
        srid = request.query_params.get("srid", None)
        # If mobile_units true, include all mobileunits that belongs to the group.
        mobile_units = request.query_params.get("mobile_units", False)
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
        if mobile_units:
            serializer_class = MobileUnitGroupUnitsSerializer
        else:
            serializer_class = MobileUnitGroupSerializer

        serializer = serializer_class(page, many=True, context={"srid":srid})
        return self.get_paginated_response(serializer.data)


class MobileUnitViewSet(viewsets.ReadOnlyModelViewSet):
    
    queryset = MobileUnit.objects.all()
    serializer_class = MobileUnitSerializer     
        
    def retrieve(self, request, pk=None):
        try:
            unit = MobileUnit.objects.get(pk=pk)
        except MobileUnit.DoesNotExist:
            return Response("MobileUnit does not exist.", status=status.HTTP_400_BAD_REQUEST)
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
        return self.get_paginated_response(serializer.data)


class GroupTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer
  

class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer


