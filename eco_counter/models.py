from datetime import datetime

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.timezone import now

TRAFFIC_COUNTER_START_YEAR = 2015
# Manually define the end year, as the source data comes from the page
# defined in env variable TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL.
# Change end year when data for the next year is available.
TRAFFIC_COUNTER_END_YEAR = 2022
ECO_COUNTER_START_YEAR = 2020
LAM_COUNTER_START_YEAR = 2010


TRAFFIC_COUNTER = "TC"
ECO_COUNTER = "EC"
LAM_COUNTER = "LC"
CSV_DATA_SOURCES = (
    (TRAFFIC_COUNTER, "TrafficCounter"),
    (ECO_COUNTER, "EcoCounter"),
    (LAM_COUNTER, "LamCounter"),
)
COUNTER_START_YEARS = {
    ECO_COUNTER: ECO_COUNTER_START_YEAR,
    TRAFFIC_COUNTER: TRAFFIC_COUNTER_START_YEAR,
    LAM_COUNTER: LAM_COUNTER_START_YEAR,
}


class ImportState(models.Model):
    current_year_number = models.PositiveSmallIntegerField(
        default=ECO_COUNTER_START_YEAR
    )
    current_month_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)], default=1
    )
    csv_data_source = models.CharField(
        max_length=2,
        choices=CSV_DATA_SOURCES,
        default=ECO_COUNTER,
    )


class Station(models.Model):

    name = models.CharField(max_length=64)
    geom = models.PointField(srid=settings.DEFAULT_SRID)
    csv_data_source = models.CharField(
        max_length=2,
        choices=CSV_DATA_SOURCES,
        default=ECO_COUNTER,
    )
    # For lam stations store the LAM station ID, this is
    # required when fetching data from the API using the ID.
    lam_id = models.PositiveSmallIntegerField(null=True)

    def __str__(self):
        return "%s %s" % (self.name, self.geom)

    class Meta:
        ordering = ["id"]


class CounterData(models.Model):
    value_ak = models.PositiveIntegerField(default=0)
    value_ap = models.PositiveIntegerField(default=0)
    value_at = models.PositiveIntegerField(default=0)
    value_pk = models.PositiveIntegerField(default=0)
    value_pp = models.PositiveIntegerField(default=0)
    value_pt = models.PositiveIntegerField(default=0)
    value_jk = models.PositiveIntegerField(default=0)
    value_jp = models.PositiveIntegerField(default=0)
    value_jt = models.PositiveIntegerField(default=0)
    value_bk = models.PositiveIntegerField(default=0)
    value_bp = models.PositiveIntegerField(default=0)
    value_bt = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True


class Year(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="years", null=True
    )
    year_number = models.PositiveSmallIntegerField(default=datetime.now().year)

    @property
    def num_days(self):
        return self.days.all().count()

    def __str__(self):
        return "%s" % (self.year_number)

    class Meta:
        ordering = ["-year_number"]


class Month(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="months", null=True
    )
    year = models.ForeignKey("Year", on_delete=models.CASCADE, related_name="months")
    month_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)], default=1
    )

    @property
    def num_days(self):
        return self.days.all().count()

    def __str__(self):
        return "%s" % (self.month_number)

    class Meta:
        ordering = ["-year__year_number", "-month_number"]


class Week(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="weeks"
    )
    week_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(53)]
    )
    years = models.ManyToManyField(Year)

    @property
    def num_days(self):
        return self.days.all().count()

    def __str__(self):
        return "%s" % (self.week_number)

    class Meta:
        ordering = ["-week_number"]


class Day(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="day", null=True
    )
    date = models.DateField(default=now)
    weekday_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)], default=1
    )
    week = models.ForeignKey(
        "Week", on_delete=models.CASCADE, related_name="days", null=True
    )
    month = models.ForeignKey(
        "Month", on_delete=models.CASCADE, related_name="days", null=True
    )
    year = models.ForeignKey(
        "Year", on_delete=models.CASCADE, related_name="days", null=True
    )

    class Meta:
        ordering = ["-date"]


class YearData(CounterData):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="year_data", null=True
    )
    year = models.ForeignKey(
        "Year", on_delete=models.CASCADE, related_name="year_data", null=True
    )

    class Meta:
        ordering = ["-year__year_number"]


class MonthData(CounterData):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="month_data", null=True
    )
    month = models.ForeignKey(
        "Month", on_delete=models.CASCADE, related_name="month_data", null=True
    )
    year = models.ForeignKey(
        "Year", on_delete=models.CASCADE, related_name="month_data", null=True
    )

    class Meta:
        ordering = ["-year__year_number", "-month__month_number"]


class WeekData(CounterData):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="week_data", null=True
    )
    week = models.ForeignKey(
        "Week", on_delete=models.CASCADE, related_name="week_data", null=True
    )

    class Meta:
        ordering = ["-week__week_number"]


class DayData(CounterData):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="day_data", null=True
    )
    day = models.ForeignKey(
        "Day", on_delete=models.CASCADE, related_name="day_data", null=True
    )

    class Meta:
        ordering = ["-day__date"]


# Hourly data for a day
class HourData(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="hour_data"
    )
    day = models.ForeignKey(
        "Day", on_delete=models.CASCADE, related_name="hour_data", null=True
    )
    values_ak = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_ap = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_at = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_pk = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_pp = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_pt = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_jk = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_jp = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_jt = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_bk = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_bp = ArrayField(models.PositiveSmallIntegerField(), default=list)
    values_bt = ArrayField(models.PositiveSmallIntegerField(), default=list)

    class Meta:
        ordering = ["-day__date"]
