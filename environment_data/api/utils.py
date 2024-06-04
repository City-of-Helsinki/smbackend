import django_filters

from environment_data.models import (
    DayData,
    HourData,
    MonthData,
    Station,
    WeekData,
    YearData,
)


class StationFilterSet(django_filters.FilterSet):
    geo_id = django_filters.NumberFilter(field_name="geo_id", lookup_expr="exact")
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Station
        fields = {"data_type": ["exact"]}


class BaseFilterSet(django_filters.FilterSet):

    station_id = django_filters.NumberFilter(field_name="station")

    class Meta:
        fields = {"station": ["exact"]}

    def get_date(self, year_number, month_and_day):
        return f"{year_number}-{month_and_day}"


class YearDataFilterSet(django_filters.FilterSet):
    station_id = django_filters.NumberFilter(field_name="station")
    start = django_filters.NumberFilter(
        field_name="year__year_number", lookup_expr="gte"
    )
    end = django_filters.NumberFilter(field_name="year__year_number", lookup_expr="lte")

    class Meta:
        model = YearData
        fields = {"station": ["exact"]}


class MonthDataFilterSet(BaseFilterSet):
    def filter_year(self, queryset, field, year):
        return queryset.filter(month__year__year_number=year)

    year = django_filters.NumberFilter(method="filter_year")
    start = django_filters.NumberFilter(
        field_name="month__month_number", lookup_expr="gte"
    )
    end = django_filters.NumberFilter(
        field_name="month__month_number", lookup_expr="lte"
    )

    class Meta:
        model = MonthData
        fields = BaseFilterSet.Meta.fields


class WeekDataFilterSet(BaseFilterSet):
    def filter_year(self, queryset, field, year):
        return queryset.filter(week__years__year_number=year)

    year = django_filters.NumberFilter(method="filter_year")
    start = django_filters.NumberFilter(
        field_name="week__week_number", lookup_expr="gte"
    )
    end = django_filters.NumberFilter(field_name="week__week_number", lookup_expr="lte")

    class Meta:
        model = WeekData
        fields = BaseFilterSet.Meta.fields


class DateDataFilterSet(BaseFilterSet):
    DATE_MODEL_NAME = None
    YEAR_LOOKUP = None

    def filter_year(self, queryset, field, year):
        return queryset.filter(**{f"{self.DATE_MODEL_NAME}__year__year_number": year})

    def filter_start(self, queryset, field, start):
        first = queryset.first()
        if first:
            lookup = first
            if self.YEAR_LOOKUP:
                lookup = getattr(first, self.YEAR_LOOKUP)
            date = self.get_date(lookup.day.year.year_number, start)
            return queryset.filter(**{f"{self.DATE_MODEL_NAME}__date__gte": date})
        else:
            return queryset.none()

    def filter_end(self, queryset, field, end):
        first = queryset.first()
        if first:
            lookup = first
            if self.YEAR_LOOKUP:
                lookup = getattr(first, self.YEAR_LOOKUP)
            date = self.get_date(lookup.day.year.year_number, end)
            return queryset.filter(**{f"{self.DATE_MODEL_NAME}__date__lte": date})
        else:
            return queryset.none()

    year = django_filters.NumberFilter(method="filter_year")
    start = django_filters.CharFilter(method="filter_start")
    end = django_filters.CharFilter(method="filter_end")


class DayDataFilterSet(DateDataFilterSet):

    DATE_MODEL_NAME = "day"

    class Meta:
        model = DayData
        fields = BaseFilterSet.Meta.fields


class HourDataFilterSet(DateDataFilterSet):

    DATE_MODEL_NAME = "hour__day"
    YEAR_LOOKUP = "hour"

    class Meta:
        model = HourData
        fields = BaseFilterSet.Meta.fields
