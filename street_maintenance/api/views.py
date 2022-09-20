from django.core.exceptions import ValidationError
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from street_maintenance.api.serializers import (
    ActiveEventSerializer,
    MaintenanceUnitSerializer,
    MaintenanceWorkSerializer,
)
from street_maintenance.models import MaintenanceUnit, MaintenanceWork


class ActiveEventsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = MaintenanceWork.objects.order_by().distinct("events")
    serializer_class = ActiveEventSerializer


class MaintenanceWorkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaintenanceWork.objects.all()
    serializer_class = MaintenanceWorkSerializer

    def list(self, request):
        queryset = MaintenanceWork.objects.all()
        filters = self.request.query_params

        if "event" in filters:
            queryset = MaintenanceWork.objects.filter(
                events__contains=[filters["event"]]
            )

        if "start_date_time" in filters:
            start_date_time = filters["start_date_time"]
            try:
                queryset = queryset.filter(timestamp__gte=start_date_time)
            except ValidationError:
                return Response(
                    "'start_date_time' must be in format YYYY--MM-DD HH:MM e.g.,'2022-09-18 10:00'",
                    status=status.HTTP_400_BAD_REQUEST,
                )

        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


class MaintenanceUnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaintenanceUnit.objects.all()
    serializer_class = MaintenanceUnitSerializer
