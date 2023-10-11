from datetime import date, timedelta

from django.db.models import Q
from rest_framework import serializers

from ..models import (
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

VALUE_FIELDS = [
    "value_ak",
    "value_ap",
    "value_at",
    "value_pk",
    "value_pp",
    "value_pt",
    "value_jk",
    "value_jp",
    "value_jt",
    "value_bk",
    "value_bp",
    "value_bt",
]
Q_EXP = Q(value_at__gt=0) | Q(value_pt__gt=0) | Q(value_jt__gt=0) | Q(value_bt__gt=0)


class StationSerializer(serializers.ModelSerializer):
    x = serializers.SerializerMethodField()
    y = serializers.SerializerMethodField()
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    sensor_types = serializers.SerializerMethodField()
    data_from_year = serializers.SerializerMethodField()
    data_until_date = serializers.SerializerMethodField()
    data_from_date = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = [
            "id",
            "name",
            "name_fi",
            "name_sv",
            "name_en",
            "csv_data_source",
            "location",
            "geometry",
            "x",
            "y",
            "lon",
            "lat",
            "sensor_types",
            "data_from_year",
            "data_until_date",
            "data_from_date",
            "is_active",
        ]

    def get_y(self, obj):
        return obj.location.y

    def get_lat(self, obj):
        obj.location.transform(4326)
        return obj.location.y

    def get_x(self, obj):
        return obj.location.x

    def get_lon(self, obj):
        obj.location.transform(4326)
        return obj.location.x

    def get_sensor_types(self, obj):
        # Return the sensor types(car, bike etc) that has a total year value >0.
        # i.e., there are sensors for counting the type of data.
        types = ["at", "pt", "jt", "bt"]
        result = []
        for type in types:
            filter = {"station": obj, f"value_{type}__gt": 0}
            if YearData.objects.filter(**filter).count() > 0:
                result.append(type)
        return result

    def get_data_from_year(self, obj):
        qs = YearData.objects.filter(Q_EXP, station=obj).order_by("year__year_number")
        if qs.count() > 0:
            return qs[0].year.year_number
        else:
            return None

    def get_is_active(self, obj):
        num_days = [1, 7, 30, 365]
        res = {}
        for days in num_days:
            from_date = date.today() - timedelta(days=days - 1)
            day_qs = Day.objects.filter(station=obj, date__gte=from_date)
            day_data_qs = DayData.objects.filter(day__in=day_qs)
            if day_data_qs.filter(Q_EXP).count() > 0:
                res[days] = True
            else:
                res[days] = False
        return res

    def get_data_until_date(self, obj):
        try:
            return (
                DayData.objects.filter(Q_EXP, station=obj).latest("day__date").day.date
            )
        except DayData.DoesNotExist:
            return None

    def get_data_from_date(self, obj):
        try:
            return (
                DayData.objects.filter(Q_EXP, station=obj)
                .earliest("day__date")
                .day.date
            )
        except DayData.DoesNotExist:
            return None


class YearSerializer(serializers.ModelSerializer):
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = Year
        fields = [
            "id",
            "station",
            "station_name",
            "year_number",
            "num_days",
        ]


class YearInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ["id", "year_number"]


class DaySerializer(serializers.ModelSerializer):
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = Day
        fields = [
            "id",
            "station",
            "station_name",
            "date",
            "weekday_number",
            "week",
            "month",
            "year",
        ]


class DayInfoSerializer(serializers.ModelSerializer):
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = Day
        fields = ["station_name", "date", "weekday_number"]


class WeekSerializer(serializers.ModelSerializer):
    years = YearInfoSerializer(many=True, read_only=True)

    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = Week
        fields = [
            "id",
            "station",
            "station_name",
            "week_number",
            "years",
            "num_days",
        ]


class WeekInfoSerializer(serializers.ModelSerializer):
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )
    years = YearInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = [
            "station_name",
            "week_number",
            "years",
        ]


class MonthSerializer(serializers.ModelSerializer):
    year_number = serializers.PrimaryKeyRelatedField(
        many=False, source="year.year_number", read_only=True
    )
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = Month
        fields = [
            "id",
            "station",
            "station_name",
            "month_number",
            "year_number",
            "num_days",
        ]


class MonthInfoSerializer(serializers.ModelSerializer):
    year_number = serializers.PrimaryKeyRelatedField(
        many=False, source="year.year_number", read_only=True
    )
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = Month
        fields = ["station_name", "month_number", "year_number"]


class YearInfoSerializer(serializers.ModelSerializer):
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = Year
        fields = ["station_name", "year_number"]


class HourDataSerializer(serializers.ModelSerializer):
    day_info = DayInfoSerializer(source="day")

    class Meta:
        model = HourData
        fields = [
            "id",
            "station",
            "day_info",
            "values_ak",
            "values_ap",
            "values_at",
            "values_pk",
            "values_pp",
            "values_pt",
            "values_jk",
            "values_jp",
            "values_jt",
        ]


class DayDataSerializer(serializers.ModelSerializer):
    day_info = DayInfoSerializer(source="day")

    class Meta:
        model = DayData
        fields = [
            "id",
            "station",
            "day_info",
        ] + VALUE_FIELDS


class WeekDataSerializer(serializers.ModelSerializer):
    week_info = WeekInfoSerializer(source="week")

    class Meta:
        model = WeekData
        fields = [
            "id",
            "station",
            "week_info",
        ] + VALUE_FIELDS


class MonthDataSerializer(serializers.ModelSerializer):
    month_info = MonthInfoSerializer(source="month")

    class Meta:
        model = MonthData
        fields = [
            "id",
            "station",
            "month_info",
        ] + VALUE_FIELDS


class YearDataSerializer(serializers.ModelSerializer):
    year_info = YearInfoSerializer(source="year")

    class Meta:
        model = YearData
        fields = [
            "id",
            "station",
            "year_info",
        ] + VALUE_FIELDS
