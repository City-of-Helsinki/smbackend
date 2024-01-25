from datetime import datetime

from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.pagination import PageNumberPagination

from street_maintenance.api.serializers import (
    ActiveEventSerializer,
    GeometryHistorySerializer,
    MaintenanceUnitSerializer,
    MaintenanceWorkSerializer,
)
from street_maintenance.management.commands.constants import (
    EVENT_CHOICES,
    PROVIDERS,
    START_DATE_TIME_FORMAT,
)
from street_maintenance.models import GeometryHistory, MaintenanceUnit, MaintenanceWork

EXAMPLE_TIME_FORMAT = "YYYY-MM-DD HH:MM:SS"
EXAMPLE_TIME = "2022-09-18 10:00:00"
EVENT_PARAM = OpenApiParameter(
    name="event",
    location=OpenApiParameter.QUERY,
    description=(
        "Return objects of given event. "
        f'Event choices are: {", ".join(EVENT_CHOICES).lower()}, '
        'E.g. "auraus".'
    ),
    required=False,
    type=str,
)
PROVIDER_PARAM = OpenApiParameter(
    name="provider",
    location=OpenApiParameter.QUERY,
    description=("Return objects of given provider. " 'E.g. "INFRAROAD".'),
    required=False,
    type=str,
)
START_DATE_TIME_PARAM = OpenApiParameter(
    name="start_date_time",
    location=OpenApiParameter.QUERY,
    description=(
        "Get objects with timestamp newer than the start_date_time. "
        f'The format for the timestamp is: {EXAMPLE_TIME_FORMAT}, e.g. "{EXAMPLE_TIME}".'
    ),
    required=False,
    type=str,
)


class LargeResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class to allow all results in one page.
    """

    page_size_query_param = "page_size"
    # Works are fetched to the remote data storage on a single page, to prevent
    # duplicates.
    max_page_size = 200_000


class ActiveEventsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = MaintenanceWork.objects.order_by().distinct("events")
    serializer_class = ActiveEventSerializer


_maintenance_works_list_parameters = [
    EVENT_PARAM,
    PROVIDER_PARAM,
    START_DATE_TIME_PARAM,
]


@extend_schema_view(
    list=extend_schema(
        parameters=_maintenance_works_list_parameters,
        description="A MaintenanceWork object is a single work performed by a provider. The geometry can be a point "
        "or a linestring. The geometry and timestamp are assigned directly from the source data. The "
        "original_event_names contains the names of the events in the source data and the events field is the mapped "
        "names. Note, if the geometry is a point, the latitude and longitude will be separately serialized. If the "
        "geometry is a linestring a separate list of coordinates will be serialized.",
    )
)
class MaintenanceWorkViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MaintenanceWorkSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = MaintenanceWork.objects.all()
        filters = self.request.query_params

        if "provider" in filters:
            provider = filters["provider"].upper()
            if provider in PROVIDERS:
                queryset = queryset.filter(maintenance_unit__provider=provider)
            else:
                raise ParseError(f"Providers are: {', '.join(PROVIDERS)}")

        if "event" in filters:
            queryset = queryset.filter(events__contains=[filters["event"]])
        if "start_date_time" in filters:
            start_date_time = filters["start_date_time"]
            try:
                start_date_time = datetime.strptime(
                    start_date_time, START_DATE_TIME_FORMAT
                )
            except ValueError:
                raise ParseError(
                    f"'start_date_time' must be in format {EXAMPLE_TIME_FORMAT} elem.g.,'{EXAMPLE_TIME}'"
                )

            queryset = queryset.filter(timestamp__gte=make_aware(start_date_time))
        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        filters = self.request.query_params
        if "unit_id" in filters:
            unit_id = filters["unit_id"]
            queryset = queryset.filter(maintenance_unit__unit_id=unit_id)

        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        description="MaintananceUnit objets are the entities that creates the MaintenanceWorks. Every MaintenanceWork "
        "has a relation to a MaintenanceUnit. The type of the MaintenanceUnit can vary depending on the provider. It "
        "can be a machine or a event",
    ),
)
class MaintenanceUnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaintenanceUnit.objects.all()
    serializer_class = MaintenanceUnitSerializer


_geometry_history_list_parameters = [
    PROVIDER_PARAM,
    EVENT_PARAM,
    START_DATE_TIME_PARAM,
]


@extend_schema_view(
    list=extend_schema(
        parameters=_geometry_history_list_parameters,
        description="GeometryHistory objects are processed from MaintenanceWork objects. MaintenanceWorks with "
        "linestrings are validated and if valid a GeometryHistory object is created with the linestring geometry. "
        "From MaintenanceWork objects that cointains point data linestrings are generated. The linestrings are "
        "generated by comparing the timestamp, event, distance and provider. For every valid generated linestring a "
        "GeometryHistory object is created. The coordinates are in SRID 4326.",
    )
)
class GeometryHitoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GeometryHistorySerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = GeometryHistory.objects.all()
        filters = self.request.query_params

        if "provider" in filters:
            provider = filters["provider"].upper()
            if provider in PROVIDERS:
                queryset = queryset.filter(provider=provider)
            else:
                raise ParseError(f"Providers are: {', '.join(PROVIDERS)}")

        if "event" in filters:
            queryset = queryset.filter(events__contains=[filters["event"]])
        if "start_date_time" in filters:
            start_date_time = filters["start_date_time"]
            try:
                start_date_time = datetime.strptime(
                    start_date_time, "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                raise ParseError(
                    f"'start_date_time' must be in format {EXAMPLE_TIME_FORMAT}  elem.g.,'{EXAMPLE_TIME}'"
                )
            queryset = queryset.filter(timestamp__gte=make_aware(start_date_time))
        return queryset

    @method_decorator(cache_page(60 * 15))
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)
