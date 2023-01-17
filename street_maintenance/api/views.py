from datetime import datetime
from functools import lru_cache

import pytz
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
    PROVIDERS,
    START_DATE_TIME_FORMAT,
)
from street_maintenance.models import GeometryHistory, MaintenanceUnit, MaintenanceWork

UTC_TIMEZONE = pytz.timezone("UTC")

# Default is 3minutes 3*60s
DEFAULT_MAX_WORK_LENGTH = 180


class LargeResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class to allow all results in one page.
    """

    page_size_query_param = "page_size"
    max_page_size = 50_000


class ActiveEventsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = MaintenanceWork.objects.order_by().distinct("events")
    serializer_class = ActiveEventSerializer


class MaintenanceWorkViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MaintenanceWorkSerializer

    def get_queryset(self):
        queryset = MaintenanceWork.objects.all()
        filters = self.request.query_params

        if "event" in filters:
            queryset = MaintenanceWork.objects.filter(
                events__contains=[filters["event"]]
            )
        if "start_date_time" in filters:
            start_date_time = filters["start_date_time"]
            try:
                start_date_time = datetime.strptime(
                    start_date_time, START_DATE_TIME_FORMAT
                )
            except ValueError:
                raise ParseError(
                    "'start_date_time' must be in format YYYY-MM-DD HH:MM:SS elem.g.,'2022-09-18 10:00:00'"
                )
            start_date_time = start_date_time.replace(tzinfo=UTC_TIMEZONE)
            queryset = queryset.filter(timestamp__gte=start_date_time)
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


class MaintenanceUnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaintenanceUnit.objects.all()
    serializer_class = MaintenanceUnitSerializer


class GeometryHitoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GeometryHistorySerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = GeometryHistory.objects.all()
        filters = self.request.query_params

        if "provider" in filters:
            provider = filters["provider"].upper()
            queryset = queryset.filter(provider=provider)
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
                    "'start_date_time' must be in format YYYY-MM-DD HH:MM:SS elem.g.,'2022-09-18 10:00:00'"
                )
            start_date_time = start_date_time.replace(tzinfo=UTC_TIMEZONE)
            queryset = queryset.filter(timestamp__gte=start_date_time)
        return queryset

    @lru_cache(maxsize=16)
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)
