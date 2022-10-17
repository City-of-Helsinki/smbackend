from datetime import datetime

from django.contrib.gis.geos import LineString
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from street_maintenance.api.serializers import (
    ActiveEventSerializer,
    HistoryGeometrySerializer,
    MaintenanceUnitSerializer,
    MaintenanceWorkSerializer,
)
from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit, MaintenanceWork

# Default is 30minutes 30*60s
DEFAULT_MAX_WORK_LENGTH = 1800


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
                datetime.strptime(start_date_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ParseError(
                    "'start_date_time' must be in format YYYY--MM-DD HH:MM elem.g.,'2022-09-18 10:00'"
                )
            queryset = queryset.filter(timestamp__gte=start_date_time)
        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        filters = self.request.query_params
        if "unit_id" in filters:
            try:
                unit_id = int(request.query_params["unit_id"])
            except ValueError:
                return Response(
                    "'unit_id' must be a integer.",
                )
            queryset = queryset.filter(maintenance_unit__unit_id=unit_id)

        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def get_geometry_history(self, request):
        """
        Returns linestrings(if two or more points(works) can be determined to belong to the same uniform work)
        and/or points for works that can not be determined to belong to a uniform work(linestring).
        """
        queryset = self.get_queryset()
        filters = self.request.query_params

        if "event" not in filters:
            raise ParseError("'get_geometry_history' requires the 'event' argument.")

        if "max_work_length" in filters:
            try:
                max_work_length = int(filters.get("max_work_length"))
            except ValueError:
                raise ParseError("'max_work_length' needs to be of type integer.")
        else:
            max_work_length = DEFAULT_MAX_WORK_LENGTH
        queryset = self.get_queryset()
        geometries = []
        elements_to_remove = []
        # Add works that are linestrings,
        for elem in queryset:
            if isinstance(elem.geometry, LineString):
                geometries.append(elem.geometry)
                elements_to_remove.append(elem.id)
        # Remove the linestring elements, as they are not needed when generaintg
        # linestrings from point data
        queryset = queryset.exclude(id__in=elements_to_remove)
        unit_ids = (
            queryset.order_by("maintenance_unit_id")
            .values_list("maintenance_unit_id", flat=True)
            .distinct("maintenance_unit_id")
        )
        for unit_id in unit_ids:
            # Temporary store points to list for LineString creation
            points = []
            qs = queryset.filter(maintenance_unit_id=unit_id).order_by("timestamp")
            prev_timestamp = None
            for elem in qs:
                if prev_timestamp:
                    delta_time = elem.timestamp - prev_timestamp
                    # If delta_time is bigger than the max_work_length, then we can assume
                    # that the work should not be in the same linestring/point.
                    if delta_time.seconds > max_work_length:
                        if len(points) > 1:
                            geometries.append(LineString(points, srid=DEFAULT_SRID))
                        else:
                            geometries.append(elem.geometry)
                        points = []

                points.append(elem.geometry)
                prev_timestamp = elem.timestamp
            if len(points) > 1:
                geometries.append(LineString(points, srid=DEFAULT_SRID))
            else:
                geometries.append(elem.geometry)

        # Create objects for every geometry to the serializer
        if geometries:
            data = []
            for geometry in geometries:
                elem = {}
                elem["event"] = request.query_params["event"]
                if isinstance(geometry, LineString):
                    elem["name"] = "LineString"
                else:
                    elem["name"] = "Point"

                elem["coordinates"] = geometry.coords
                data.append(elem)
        else:
            data = []

        results = HistoryGeometrySerializer(data, many=True).data
        return Response(results)


class MaintenanceUnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MaintenanceUnit.objects.all()
    serializer_class = MaintenanceUnitSerializer
