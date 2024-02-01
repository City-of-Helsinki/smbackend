import sys

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from ..models import (
    CSV_DATA_SOURCES,
    Day,
    DayData,
    HourData,
    Month,
    MonthData,
    Station,
    Week,
    WeekData,
    Year,
    YearData,
)
from .serializers import (
    DayDataSerializer,
    DaySerializer,
    HourDataSerializer,
    MonthDataSerializer,
    MonthSerializer,
    StationSerializer,
    WeekDataSerializer,
    WeekSerializer,
    YearDataSerializer,
    YearSerializer,
)

NOT_FOUND_RESPONSE_MSG = "Not found."


def get_serialized_data_by_date(class_name, query_params):
    data_class = getattr(sys.modules[__name__], class_name)
    serializer_class = getattr(sys.modules[__name__], class_name + "Serializer")
    date = query_params.get("date", None)
    station_id = query_params.get("station_id", None)
    if date is None or station_id is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        queryset = data_class.objects.get(station_id=station_id, day__date=date)
    except data_class.DoesNotExist:
        return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)

    serializer = serializer_class(queryset, many=False)
    return serializer


class StationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer

    @method_decorator(cache_page(60 * 60))
    def list(self, request):
        queryset = Station.objects.all()
        filters = self.request.query_params
        if "counter_type" in filters:
            counter_type = filters["counter_type"]
            if counter_type in str(CSV_DATA_SOURCES):
                queryset = Station.objects.filter(csv_data_source=counter_type)
            else:
                raise ParseError(
                    "Valid 'counter_type' choices are: 'EC', 'TC', 'TR' or 'LC'."
                )
        if "data_type" in filters:
            data_type = filters["data_type"].lower()
            data_types = ["a", "j", "b", "p"]
            if data_type not in data_types:
                raise ParseError(
                    f"Valid 'data_type' choices are: {', '.join(data_types)}"
                )
            ids = []
            data_type = data_type + "t"
            for station in Station.objects.all():
                filter = {"station": station, f"value_{data_type}__gt": 0}
                if YearData.objects.filter(**filter).count() > 0:
                    ids.append(station.id)
            queryset = Station.objects.filter(id__in=ids)

        page = self.paginate_queryset(queryset)
        serializer = StationSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class HourDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HourData.objects.all()
    serializer_class = HourDataSerializer

    @action(detail=False, methods=["get"])
    def get_hour_data(self, request):
        serializer = get_serialized_data_by_date("HourData", request.query_params)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DayDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DayData.objects.all()
    serializer_class = DayDataSerializer

    @action(detail=False, methods=["get"])
    def get_day_data(self, request):
        serializer = get_serialized_data_by_date("DayData", request.query_params)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def get_day_datas(self, request):
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)
        station_id = request.query_params.get("station_id", None)
        if start_date is None or end_date is None or station_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = DayData.objects.filter(
                station_id=station_id,
                day__date__gte=start_date,
                day__date__lte=end_date,
            ).order_by("day__date")
        except DayData.DoesNotExist:
            return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)

        serializer = DayDataSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WeekDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeekData.objects.all()
    serializer_class = WeekDataSerializer

    @action(detail=False, methods=["get"])
    def get_week_data(self, request):
        week_number = request.query_params.get("week_number", None)
        year_number = request.query_params.get("year_number", None)
        station_id = request.query_params.get("station_id", None)
        if station_id is None or week_number is None or year_number is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = WeekData.objects.get(
                station_id=station_id,
                week__week_number=week_number,
                week__years__year_number=year_number,
            )
        except WeekData.DoesNotExist:
            return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)

        serializer = WeekDataSerializer(queryset, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def get_week_datas(self, request):
        start_week_number = request.query_params.get("start_week_number", None)
        end_week_number = request.query_params.get("end_week_number", None)
        year_number = request.query_params.get("year_number", None)
        station_id = request.query_params.get("station_id", None)
        if (
            start_week_number is None
            or end_week_number is None
            or year_number is None
            or station_id is None
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = WeekData.objects.filter(
                station_id=station_id,
                week__week_number__gte=start_week_number,
                week__week_number__lte=end_week_number,
                week__years__year_number=year_number,
            ).order_by("week__week_number")
        except WeekData.DoesNotExist:
            return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)
        serializer = WeekDataSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonthDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonthData.objects.all()
    serializer_class = MonthDataSerializer

    @action(detail=False, methods=["get"])
    def get_month_data(self, request):
        month_number = request.query_params.get("month_number", None)
        year_number = request.query_params.get("year_number", None)
        station_id = request.query_params.get("station_id", None)
        if station_id is None or month_number is None or year_number is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = MonthData.objects.get(
                station_id=station_id,
                month__month_number=month_number,
                month__year__year_number=year_number,
            )
        except MonthData.DoesNotExist:
            return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)

        serializer = MonthDataSerializer(queryset, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def get_month_datas(self, request):
        start_month_number = request.query_params.get("start_month_number", None)
        end_month_number = request.query_params.get("end_month_number", None)
        year_number = request.query_params.get("year_number", None)
        station_id = request.query_params.get("station_id", None)
        if (
            start_month_number is None
            or end_month_number is None
            or year_number is None
            or station_id is None
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = MonthData.objects.filter(
                station_id=station_id,
                month__month_number__gte=start_month_number,
                month__month_number__lte=end_month_number,
                month__year__year_number=year_number,
            ).order_by("month__month_number")
        except MonthData.DoesNotExist:
            return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)

        serializer = MonthDataSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class YearDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = YearData.objects.all()
    serializer_class = YearDataSerializer

    @action(detail=False, methods=["get"])
    def get_year_data(self, request):
        year_number = request.query_params.get("year_number", None)
        station_id = request.query_params.get("station_id", None)
        if station_id is None or year_number is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = YearData.objects.get(
                station_id=station_id, year__year_number=year_number
            )
        except YearData.DoesNotExist:
            return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)

        serializer = YearDataSerializer(queryset, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def get_year_datas(self, request):
        start_year_number = request.query_params.get("start_year_number", None)
        end_year_number = request.query_params.get("end_year_number", None)
        station_id = request.query_params.get("station_id", None)
        if start_year_number is None or end_year_number is None or station_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            queryset = YearData.objects.filter(
                station_id=station_id,
                year__year_number__gte=start_year_number,
                year__year_number__lte=end_year_number,
            ).order_by("year__year_number")
        except YearData.DoesNotExist:
            return Response(NOT_FOUND_RESPONSE_MSG, status=status.HTTP_400_BAD_REQUEST)

        serializer = YearDataSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DayViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Day.objects.all()
    serializer_class = DaySerializer


class WeekViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Week.objects.all()
    serializer_class = WeekSerializer


class MonthViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Month.objects.all()
    serializer_class = MonthSerializer


class YearViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Year.objects.all()
    serializer_class = YearSerializer
