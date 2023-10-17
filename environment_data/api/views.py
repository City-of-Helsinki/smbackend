from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.response import Response

from environment_data.api.constants import (
    DATA_TYPES,
    DATETIME_FORMATS,
    ENVIRONMENT_DATA_PARAMS,
    ENVIRONMENT_STATION_PARAMS,
)
from environment_data.api.serializers import (
    DayDataSerializer,
    HourDataSerializer,
    MonthDataSerializer,
    ParameterSerializer,
    StationSerializer,
    WeekDataSerializer,
    YearDataSerializer,
)
from environment_data.constants import DATA_TYPES_LIST, VALID_DATA_TYPE_CHOICES
from environment_data.models import (
    DayData,
    HourData,
    MonthData,
    Parameter,
    Station,
    WeekData,
    YearData,
)

from .utils import get_start_and_end_and_year


@extend_schema_view(
    list=extend_schema(
        description="Environment data stations",
        parameters=ENVIRONMENT_STATION_PARAMS,
    )
)
class StationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        filters = self.request.query_params
        data_type = filters.get("data_type", None)
        if data_type:
            data_type = str(data_type).upper()
            if data_type not in DATA_TYPES_LIST:
                return Response(
                    f"Invalid data type, valid types are: {VALID_DATA_TYPE_CHOICES}",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(data_type=data_type)

        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        description="Environment data parameters",
    )
)
class ParameterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=ENVIRONMENT_DATA_PARAMS,
        description="Returns yearly, monthly, weekly or daily means of measured parameters."
        " Returns also the hourly measured parameters from which the means are calculated."
        " Provide the 'type' parameter to choose what type of data to return.",
    )
)
class DataViewSet(viewsets.GenericViewSet):
    queryset = YearData.objects.all()

    def list(self, request, *args, **kwargs):
        filters = self.request.query_params
        station_id = filters.get("station_id", None)
        if not station_id:
            return Response(
                "Supply 'station_id' parameter.", status=status.HTTP_400_BAD_REQUEST
            )
        else:
            try:
                station = Station.objects.get(id=station_id)
            except Station.DoesNotExist:
                return Response(
                    f"Station with id {station_id} not found.",
                    status=status.HTTP_400_BAD_REQUEST,
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
                    station=station,
                    hour__day__year__year_number=year,
                    hour__day__date__gte=start,
                    hour__day__date__lte=end,
                )
                serializer_class = HourDataSerializer
            case DATA_TYPES.DAY:
                queryset = DayData.objects.filter(
                    station=station,
                    day__date__gte=start,
                    day__date__lte=end,
                    day__year__year_number=year,
                )
                serializer_class = DayDataSerializer
            case DATA_TYPES.WEEK:
                serializer_class = WeekDataSerializer
                queryset = WeekData.objects.filter(
                    week__years__year_number=year,
                    station=station,
                    week__week_number__gte=start,
                    week__week_number__lte=end,
                )
            case DATA_TYPES.MONTH:
                serializer_class = MonthDataSerializer
                queryset = MonthData.objects.filter(
                    month__year__year_number=year,
                    station=station,
                    month__month_number__gte=start,
                    month__month_number__lte=end,
                )
            case DATA_TYPES.YEAR:
                serializer_class = YearDataSerializer
                queryset = YearData.objects.filter(
                    station=station,
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
