from django.contrib import admin

from eco_counter.models import (
    DayData,
    HourData,
    ImportState,
    MonthData,
    Station,
    WeekData,
    YearData,
)


class DataAdmin(admin.ModelAdmin):
    def get_name(self, obj):
        return obj.station.name

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


class YearDataAdmin(DataAdmin):
    list_display = ("get_name", "year")


class MonthDataAdmin(DataAdmin):
    list_display = ("get_name", "month", "year")

    def year(self, obj):
        return obj.month.year.year_number


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
        return obj.day.date


class ImportStateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "csv_data_source",
        "current_year_number",
        "current_month_number",
        "current_day_number",
    )

    def get_readonly_fields(self, request, obj=None):
        return ["csv_data_source"]


class StationAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]


admin.site.register(YearData, YearDataAdmin)
admin.site.register(MonthData, MonthDataAdmin)
admin.site.register(WeekData, WeekDataAdmin)
admin.site.register(DayData, DayDataAdmin)
admin.site.register(HourData, HourDataAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(ImportState, ImportStateAdmin)
