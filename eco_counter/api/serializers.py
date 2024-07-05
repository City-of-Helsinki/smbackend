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


class YearSerializer(serializers.ModelSerializer):

    class Meta:
        model = Year
        fields = [
            "id",
            "year_number",
            "num_days",
        ]


class YearInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ["id", "year_number"]


class DaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Day
        fields = [
            "id",
            "date",
            "weekday_number",
            "week",
            "month",
            "year",
        ]


class DayInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Day
        fields = ["date", "weekday_number"]


class WeekSerializer(serializers.ModelSerializer):
    years = YearInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = [
            "id",
            "week_number",
            "years",
            "num_days",
        ]


class WeekInfoSerializer(serializers.ModelSerializer):
    years = YearInfoSerializer(many=True, read_only=True)

    class Meta:
        model = Week
        fields = [
            "week_number",
            "years",
        ]


class MonthSerializer(serializers.ModelSerializer):
    year_number = serializers.PrimaryKeyRelatedField(
        many=False, source="year.year_number", read_only=True
    )

    class Meta:
        model = Month
        fields = [
            "id",
            "month_number",
            "year_number",
            "num_days",
        ]


class MonthInfoSerializer(serializers.ModelSerializer):
    year_number = serializers.PrimaryKeyRelatedField(
        many=False, source="year.year_number", read_only=True
    )

    class Meta:
        model = Month
        fields = ["month_number", "year_number"]


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
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = DayData
        fields = [
            "id",
            "station",
            "station_name",
            "day_info",
        ] + VALUE_FIELDS


class WeekDataSerializer(serializers.ModelSerializer):
    week_info = WeekInfoSerializer(source="week")
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = WeekData
        fields = [
            "id",
            "station",
            "station_name",
            "week_info",
        ] + VALUE_FIELDS


class MonthDataSerializer(serializers.ModelSerializer):
    month_info = MonthInfoSerializer(source="month")
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = MonthData
        fields = [
            "id",
            "station",
            "station_name",
            "month_info",
        ] + VALUE_FIELDS


class YearDataSerializer(serializers.ModelSerializer):
    year_info = YearInfoSerializer(source="year")
    station_name = serializers.PrimaryKeyRelatedField(
        many=False, source="station.name", read_only=True
    )

    class Meta:
        model = YearData
        fields = [
            "id",
            "station",
            "station_name",
            "year_info",
        ] + VALUE_FIELDS
