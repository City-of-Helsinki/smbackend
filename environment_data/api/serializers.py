from rest_framework import serializers

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
    params = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = ["id", "name", "location", "geo_id", "params"]

    def get_params(self, obj):
        res = {}
        for param in obj.parameters.all():
            qs = YearData.objects.filter(
                station=obj, measurements__parameter=param, measurements__value__gte=0
            )
            if qs.count():
                res[param.name] = True
            else:
                res[param.name] = False
        return res


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = "__all__"


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
