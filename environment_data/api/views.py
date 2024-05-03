from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from environment_data.api.constants import (
    DATA_TYPES,
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
from environment_data.constants import DATA_TYPES_LIST
from environment_data.models import (
    DayData,
    HourData,
    MonthData,
    Parameter,
    Station,
    WeekData,
    YearData,
)

from .utils import (
    DayDataFilterSet,
    HourDataFilterSet,
    MonthDataFilterSet,
    StationFilterSet,
    WeekDataFilterSet,
    YearDataFilterSet,
)


@extend_schema_view(
    list=extend_schema(
        description="Environment data stations",
        parameters=ENVIRONMENT_STATION_PARAMS,
    )
)
class StationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = StationFilterSet

    @method_decorator(cache_page(60 * 60))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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

    queryset = []
    serializer_class = None

    def get_serializer_class(self):
        data_type = self.request.query_params.get("type", "").lower()
        match data_type:
            case DATA_TYPES.HOUR:
                return HourDataSerializer
            case DATA_TYPES.DAY:
                return DayDataSerializer
            case DATA_TYPES.WEEK:
                return WeekDataSerializer
            case DATA_TYPES.MONTH:
                return MonthDataSerializer
            case DATA_TYPES.YEAR:
                return YearDataSerializer
            case _:
                raise ValidationError(
                    f"Provide a valid 'type' parameter. Valid types are: {', '.join([f for f in DATA_TYPES_LIST])}",
                )

    def get_queryset(self):
        params = self.request.query_params
        data_type = params.get("type", "").lower()
        queryset = YearData.objects.all()
        match data_type:
            case DATA_TYPES.HOUR:
                filter_set = HourDataFilterSet(
                    data=params, queryset=HourData.objects.all()
                )
            case DATA_TYPES.DAY:
                filter_set = DayDataFilterSet(
                    data=params, queryset=DayData.objects.all()
                )
            case DATA_TYPES.WEEK:
                filter_set = WeekDataFilterSet(
                    data=params, queryset=WeekData.objects.all()
                )
            case DATA_TYPES.MONTH:
                filter_set = MonthDataFilterSet(
                    data=params, queryset=MonthData.objects.all()
                )
            case DATA_TYPES.YEAR:
                filter_set = YearDataFilterSet(
                    data=params, queryset=YearData.objects.all()
                )
            case _:
                raise ValidationError(
                    f"Provide a valid 'type' parameter. Valid types are: {', '.join([f for f in DATA_TYPES_LIST])}",
                )
        if filter_set and filter_set.is_valid():
            return filter_set.qs
        else:
            return queryset.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer_class()(page, many=True)
        return self.get_paginated_response(serializer.data)
