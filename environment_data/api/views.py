from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.response import Response

from environment_data.api.serializers import (
    DayDataSerializer,
    HourDataSerializer,
    MonthDataSerializer,
    ParameterSerializer,
    StationSerializer,
    WeekDataSerializer,
    YearDataSerializer,
)
from environment_data.models import (
    DayData,
    HourData,
    MonthData,
    Parameter,
    Station,
    WeekData,
    YearData,
)

from .constants import AIR_MONITORING_DATA_PARAMS, DATA_TYPES, DATETIME_FORMATS
from .utils import get_start_and_end_and_year


@extend_schema_view(
    list=extend_schema(
        description="Air monitoring stations",
    )
)
class StationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


@extend_schema_view(
    list=extend_schema(
        description="Air monitoring parameters",
    )
)
class ParameterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=AIR_MONITORING_DATA_PARAMS,
        description="Returns yearly, monthly, weekly or daily means of measured parameters."
        " Returns also the hourly measured parameters from which the means are calculated."
        " Provide the 'type' parameter to choose what type of data to return.",
    )
)
class DataViewSet(viewsets.GenericViewSet):
    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        filters = self.request.query_params
        station_id = filters.get("station_id", None)
        if not station_id:
            return Response(
                "Supply 'station_id' parameter.", status=status.HTTP_400_BAD_REQUEST
            )
        data_type = filters.get("type", None)
        if not data_type:
            return Response(
                "Supply 'type' parameter", status=status.HTTP_400_BAD_REQUEST
            )
        else:
            data_type = data_type.lower()

        start, end, year = get_start_and_end_and_year(filters, data_type)
        match data_type:
            case DATA_TYPES.HOUR:
                queryset = HourData.objects.filter(
                    station_id=station_id,
                    hour__day__year__year_number=year,
                    hour__day__date__gte=start,
                    hour__day__date__lte=end,
                )
                serializer_class = HourDataSerializer
            case DATA_TYPES.DAY:
                queryset = DayData.objects.filter(
                    station_id=station_id,
                    day__date__gte=start,
                    day__date__lte=end,
                    day__year__year_number=year,
                )
                serializer_class = DayDataSerializer
            case DATA_TYPES.WEEK:
                serializer_class = WeekDataSerializer
                queryset = WeekData.objects.filter(
                    week__years__year_number=year,
                    station_id=station_id,
                    week__week_number__gte=start,
                    week__week_number__lte=end,
                )
            case DATA_TYPES.MONTH:
                serializer_class = MonthDataSerializer
                queryset = MonthData.objects.filter(
                    month__year__year_number=year,
                    station_id=station_id,
                    month__month_number__gte=start,
                    month__month_number__lte=end,
                )
            case DATA_TYPES.YEAR:
                serializer_class = YearDataSerializer
                queryset = YearData.objects.filter(
                    station_id=station_id,
                    year__year_number__gte=start,
                    year__year_number__lte=end,
                )
            case _:
                return Response(
                    f"Provide a valid 'type' parameters. Valid types are: {', '.join([f for f in DATETIME_FORMATS])}",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        page = self.paginate_queryset(queryset)
        serializer = serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)
