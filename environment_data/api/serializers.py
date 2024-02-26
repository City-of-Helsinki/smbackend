from rest_framework import serializers

from environment_data.constants import DATA_TYPES_FULL_NAME
from environment_data.models import (
    Day,
    DayData,
    HourData,
    Measurement,
    MonthData,
    Parameter,
    Station,
    WeekData,
    YearData,
)


class StationSerializer(serializers.ModelSerializer):
    parameters_in_use = serializers.SerializerMethodField()
    data_type_verbose = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = [
            "id",
            "data_type",
            "data_type_verbose",
            "name",
            "name_sv",
            "name_en",
            "location",
            "geo_id",
            "parameters_in_use",
        ]

    def get_parameters_in_use(self, obj):
        res = {}
        available_parameters_qs = Parameter.objects.filter(data_type=obj.data_type)

        for available_parameter in available_parameters_qs:
            name = available_parameter.name
            if obj.parameters.filter(name=name).exists():
                res[name] = True
            else:
                res[name] = False
        return res

    def get_data_type_verbose(self, obj):
        return DATA_TYPES_FULL_NAME[obj.data_type]


class ParameterSerializer(serializers.ModelSerializer):
    data_type_verbose = serializers.SerializerMethodField()

    class Meta:
        model = Parameter
        fields = ["id", "data_type", "data_type_verbose", "name", "description"]

    def get_data_type_verbose(self, obj):
        return DATA_TYPES_FULL_NAME[obj.data_type]


class MeasurementSerializer(serializers.ModelSerializer):
    parameter = serializers.PrimaryKeyRelatedField(
        many=False, source="parameter.name", read_only=True
    )

    class Meta:
        model = Measurement
        fields = ["id", "value", "parameter"]


class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = "__all__"


class YearDataSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    year_number = serializers.PrimaryKeyRelatedField(
        many=False, source="year.year_number", read_only=True
    )

    class Meta:
        model = YearData
        fields = ["id", "measurements", "year_number"]


class MonthDataSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    month_number = serializers.PrimaryKeyRelatedField(
        many=False, source="month.month_number", read_only=True
    )
    year_number = serializers.PrimaryKeyRelatedField(
        many=False, source="month.year.year_number", read_only=True
    )

    class Meta:
        model = MonthData
        fields = ["id", "measurements", "month_number", "year_number"]


class WeekDataSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    week_number = serializers.PrimaryKeyRelatedField(
        many=False, source="week.week_number", read_only=True
    )

    class Meta:
        model = WeekData
        fields = ["id", "measurements", "week_number"]


class DayDataSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    date = serializers.PrimaryKeyRelatedField(
        many=False, source="day.date", read_only=True
    )

    class Meta:
        model = DayData
        fields = ["id", "measurements", "date"]


class HourDataSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True)
    hour_number = serializers.PrimaryKeyRelatedField(
        many=False, source="hour.hour_number", read_only=True
    )
    date = serializers.PrimaryKeyRelatedField(
        many=False, source="hour.day.date", read_only=True
    )

    class Meta:
        model = HourData
        fields = [
            "id",
            "measurements",
            "hour_number",
            "date",
        ]
