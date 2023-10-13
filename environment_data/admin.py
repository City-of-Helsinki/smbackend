from django.contrib import admin

from environment_data.models import (
    Day,
    DayData,
    Hour,
    HourData,
    ImportState,
    Measurement,
    Month,
    MonthData,
    Parameter,
    Station,
    Week,
    WeekData,
    Year,
    YearData,
)


class BaseAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


class DataAdmin(BaseAdmin):
    def get_name(self, obj):
        return obj.station.name

    # For optimizing purposes, if not set the admin will timeout when loading the row
    raw_id_fields = ["measurements"]


class YearDataAdmin(DataAdmin):
    list_display = ("get_name", "year")


class MonthDataAdmin(DataAdmin):
    list_display = ("get_name", "month", "year")


class WeekDataAdmin(DataAdmin):
    list_display = ("get_name", "week", "get_years")

    def get_years(self, obj):
        return [y for y in obj.week.years.all()]


class DayDataAdmin(DataAdmin):
    list_display = (
        "get_name",
        "get_date",
    )

    def get_date(self, obj):
        return obj.day.date


class HourDataAdmin(DataAdmin):
    list_display = (
        "get_name",
        "get_date",
    )

    def get_date(self, obj):
        return obj.hour.day.date


class WeekAdmin(BaseAdmin):
    list_display = (
        "week_number",
        "get_year",
    )

    def get_year(self, obj):
        return f"{', '.join([str(y.year_number) for y in obj.years.all()])} {obj.week_number}"


class YearAdmin(BaseAdmin):
    list_display = ("get_year",)

    def get_year(self, obj):
        return obj.year_number


class MonthAdmin(BaseAdmin):
    list_display = (
        "month_number",
        "get_year",
    )

    def get_year(self, obj):
        return obj.year.year_number


class DayAdmin(BaseAdmin):
    list_display = ("get_date",)

    def get_date(self, obj):
        return obj.date


class HourAdmin(BaseAdmin):
    list_display = (
        "hour_number",
        "get_date",
    )

    def get_date(self, obj):
        return obj.day.date


class ImportStateAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


class StationAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


admin.site.register(Station, StationAdmin)
admin.site.register(ImportState, ImportStateAdmin)
admin.site.register(YearData, YearDataAdmin)
admin.site.register(MonthData, MonthDataAdmin)
admin.site.register(WeekData, WeekDataAdmin)
admin.site.register(HourData, HourDataAdmin)
admin.site.register(DayData, DayDataAdmin)
admin.site.register(Year, YearAdmin)
admin.site.register(Month, MonthAdmin)
admin.site.register(Week, WeekAdmin)
admin.site.register(Day, DayAdmin)
admin.site.register(Hour, HourAdmin)
admin.site.register(Measurement)
admin.site.register(Parameter)
