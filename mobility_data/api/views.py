from distutils.util import strtobool
from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from ..models import (
    MobileUnitGroup,
    MobileUnit,
    ContentType,
    GroupType,
)
from .serializers import (
    MobileUnitGroupSerializer,
    MobileUnitGroupUnitsSerializer,
    MobileUnitSerializer,
    GroupTypeSerializer,
    ContentTypeSerializer,
)


def get_srid_and_latlon(filters):
    """
    Helper function that parses and returns the srid and latlon query params.
    """
    latlon = False
    srid = None
    if "srid" in filters:
        try:
            srid = int(filters["srid"])
        except ValueError:
            raise ParseError("'srid' must be of type integer.")

    if "latlon" in filters:
        try:
            latlon = strtobool(filters["latlon"])
        except ValueError:
            raise ParseError("'latlon' needs to be a boolean")
    return srid, latlon


def get_mobile_units(filters):
    """
    Helper function that parses and returns the mobile_units query param.
    """
    mobile_units = None
    if "mobile_units" in filters:
        try:
            mobile_units = strtobool(filters["mobile_units"])
        except ValueError:
            raise ParseError("'mobile_units' needs to be a boolean")
    return mobile_units


class MobileUnitGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MobileUnitGroup.objects.all()
    serializer_class = MobileUnitGroupSerializer

    def retrieve(self, request, pk=None):
        try:
            unit = MobileUnitGroup.objects.get(pk=pk)
        except MobileUnitGroup.DoesNotExist:
            return Response(
                "MobileUnitGroup does not exist.", status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError:
            return Response("Invalid UUID.")

        filters = self.request.query_params
        srid, latlon = get_srid_and_latlon(filters)
        mobile_units = get_mobile_units(filters)

        serializer_class = None
        if mobile_units:
            serializer_class = MobileUnitGroupUnitsSerializer
        else:
            serializer_class = MobileUnitGroupSerializer

        serializer = serializer_class(
            unit, many=False, context={"srid": srid, "latlon": latlon}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        queryset = None
        serializer = None
        filters = self.request.query_params
        srid, latlon = get_srid_and_latlon(filters)
        # If mobile_units true, include all mobileunits that belongs to the group.
        mobile_units = get_mobile_units(filters)
        if "type_name" in filters:
            type_name = filters["type_name"]
            if not GroupType.objects.filter(type_name=type_name).exists():
                return Response(
                    "type_name does not exist.", status=status.HTTP_400_BAD_REQUEST
                )
            queryset = MobileUnitGroup.objects.filter(group_type__type_name=type_name)
        else:
            queryset = MobileUnitGroup.objects.all()

        page = self.paginate_queryset(queryset)
        serializer_class = None
        if mobile_units:
            serializer_class = MobileUnitGroupUnitsSerializer
        else:
            serializer_class = MobileUnitGroupSerializer

        serializer = serializer_class(
            page, many=True, context={"srid": srid, "latlon": latlon}
        )
        return self.get_paginated_response(serializer.data)


class MobileUnitViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = MobileUnit.objects.all()
    serializer_class = MobileUnitSerializer

    def retrieve(self, request, pk=None):
        try:
            unit = MobileUnit.objects.get(pk=pk)
        except MobileUnit.DoesNotExist:
            return Response(
                "MobileUnit does not exist.", status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError:
            return Response("Invalid UUID.")

        filters = self.request.query_params
        srid, latlon = get_srid_and_latlon(filters)
        serializer = MobileUnitSerializer(
            unit, many=False, context={"srid": srid, "latlon": latlon}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        """
        Lists MobileUnits, optionally list by type_name if given
        and transforms to given srid.
        """
        queryset = None
        filters = self.request.query_params
        srid, latlon = get_srid_and_latlon(filters)
        if "type_name" in filters:
            type_name = filters["type_name"]
            if not ContentType.objects.filter(type_name=type_name).exists():
                return Response(
                    "type_name does not exist.", status=status.HTTP_400_BAD_REQUEST
                )
            queryset = MobileUnit.objects.filter(content_type__type_name=type_name)
        else:
            queryset = MobileUnit.objects.all()

        page = self.paginate_queryset(queryset)
        serializer = MobileUnitSerializer(
            page, many=True, context={"srid": srid, "latlon": latlon}
        )
        return self.get_paginated_response(serializer.data)


class GroupTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
