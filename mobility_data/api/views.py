import logging
import types

from django.contrib.gis.gdal import SpatialReference
from django.core.exceptions import ValidationError
from django.db import connection, reset_queries
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from munigeo import api as munigeo_api
from rest_framework import status, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from services.models import Unit
from services.utils import strtobool

from ..models import ContentType, GroupType, MobileUnit, MobileUnitGroup
from .serializers import (
    ContentTypeSerializer,
    GroupTypeSerializer,
    MobileUnitGroupSerializer,
    MobileUnitGroupUnitsSerializer,
    MobileUnitSerializer,
)

FIELD_TYPES = types.SimpleNamespace()
FIELD_TYPES.FLOAT = float
FIELD_TYPES.INT = int
FIELD_TYPES.BOOL = bool

logger = logging.getLogger("mobility_data")


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
            latlon = bool(strtobool(filters["latlon"]))
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
            if not GroupType.objects.filter(name=type_name).exists():
                return Response(
                    "type_name does not exist.", status=status.HTTP_400_BAD_REQUEST
                )
            queryset = MobileUnitGroup.objects.filter(group_type__name=type_name)
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
    queryset = MobileUnit.objects.filter(is_active=True)
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        only = self.request.query_params.get("only", "")
        if only:
            context["only"] = [x.strip() for x in only.split(",") if x]

        context["srid"], context["latlon"] = get_srid_and_latlon(
            self.request.query_params
        )
        context["services_unit_instances"] = self.services_unit_instances
        return context

    def get_queryset(self):
        queryset = MobileUnit.objects.filter(is_active=True)
        queryset = queryset.prefetch_related("content_types")
        unit_ids = []
        filters = self.request.query_params
        type_names = None

        if "type_name" in filters or "type_names" in filters:
            type_name = filters.get("type_name", None)
            if type_name:
                queryset = queryset.filter(content_types__type_name=type_name)
            else:
                type_names = [
                    t.strip() for t in filters.get("type_names", "").split(",")
                ]
                queryset = queryset.filter(
                    content_types__type_name__in=type_names
                ).distinct()

            # If the data locates in the services_unit table (i.e., MobileUnit has a unit_id)
            # get the unit_ids to retrieve the Units for filtering(bbox and extra)
            unit_ids = list(
                queryset.filter(unit_id__isnull=False).values_list("unit_id", flat=True)
            )
        if type_names:
            mobile_units_qs = queryset.exclude(id__in=unit_ids)
            if mobile_units_qs.count() > 0 and unit_ids:
                raise Exception(
                    "Filtering MobileUnits with ContentTypes containing MobileUnits and MobileUnits that contains"
                    " references to services_unit table is not possible."
                )

        self.services_unit_instances = True if len(unit_ids) > 0 else False
        if self.services_unit_instances:
            queryset = Unit.objects.filter(id__in=unit_ids)

        if "bbox" in filters:
            val = filters.get("bbox", None)
            geometry_field_name = (
                "location" if self.services_unit_instances else "geometry"
            )
            if val:
                ref = SpatialReference(filters.get("bbox_srid", 4326))
                bbox_geometry_filter = munigeo_api.build_bbox_filter(
                    ref, val, geometry_field_name
                )
                queryset = queryset.filter(Q(**bbox_geometry_filter))

        for filter in filters:
            if filter.startswith("extra__"):
                if "type_name" not in filters:
                    return Response(
                        "You must provide a 'type_name' argument when filtering with 'extra__' argument."
                    )
                if queryset.count() > 0:
                    value = filters[filter].strip()
                    key = filter.split("__")[1]
                    # Determine the type of the value in jsonfield and typecast argument to int
                    # or float if required. Assume all fields with same key has same value type.
                    # If not typecasted, filtering is done with string values and will not work for
                    # int or float values.
                    try:
                        field_value = queryset[0].extra[key]
                        field_type = type(field_value)
                    except KeyError:
                        return Response(
                            f"extra field '{key}' does not exist",
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    match field_type:
                        case FIELD_TYPES.FLOAT:
                            value = float(value)
                        case FIELD_TYPES.INT:
                            value = int(value)
                        case FIELD_TYPES.BOOL:
                            value = strtobool(value)
                            value = bool(value)

                    queryset = queryset.filter(**{filter: value})

        return queryset

    @method_decorator(cache_page(60 * 60))
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if logger.level <= logging.DEBUG:
            logger.debug(connection.queries)
            queries_time = sum([float(s["time"]) for s in connection.queries])
            logger.debug(
                f"MobileUnit list queries total execution time: {queries_time} Num queries: {len(connection.queries)}"
            )
            reset_queries()
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class GroupTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
