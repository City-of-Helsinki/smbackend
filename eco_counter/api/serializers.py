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
]


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
            "geom",
            "x",
            "y",
            "lon",
            "lat",
        ]

    def get_y(self, obj):
        return obj.geom.y

    def get_lat(self, obj):
        obj.geom.transform(4326)
        return obj.geom.y

    def get_x(self, obj):
        return obj.geom.x

    def get_lon(self, obj):
        obj.geom.transform(4326)
        return obj.geom.x


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
