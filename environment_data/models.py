from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.timezone import now

from .constants import AIR_QUALITY, DATA_TYPE_CHOICES


class DataTypeModel(models.Model):
    class Meta:
        abstract = True

    data_type = models.CharField(
        max_length=2,
        choices=DATA_TYPE_CHOICES,
        default=AIR_QUALITY,
    )


class ImportState(DataTypeModel):
    year_number = models.PositiveSmallIntegerField(default=2010)
    month_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        default=1,
    )


class Parameter(DataTypeModel):
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=64, null=True)

    def __str__(self):
        return self.name


class Measurement(models.Model):
    value = models.FloatField()
    parameter = models.ForeignKey(
        "Parameter", on_delete=models.CASCADE, related_name="values"
    )

    def __str__(self):
        return "%s %s" % (self.parameter.name, self.value)


class Station(DataTypeModel):
    name = models.CharField(max_length=64)
    location = models.PointField(srid=4326)
    geo_id = models.IntegerField()
    parameters = models.ManyToManyField("Parameter", related_name="stations")

    def __str__(self):
        return "%s %s" % (self.name, self.location)

    class Meta:
        ordering = ["id"]


class Year(models.Model):
    year_number = models.PositiveSmallIntegerField(default=2023)

    class Meta:
        ordering = ["-year_number"]
        indexes = [models.Index(fields=["year_number"])]

    @property
    def num_days(self):
        return self.days.count()

    def __str__(self):
        return "%s" % (self.year_number)


class Month(models.Model):
    year = models.ForeignKey("Year", on_delete=models.CASCADE, related_name="months")
    month_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)], default=1
    )

    @property
    def num_days(self):
        return self.days.count()

    def __str__(self):
        return "%s" % (self.month_number)

    class Meta:
        ordering = ["-year__year_number", "-month_number"]


class Week(models.Model):
    week_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(53)]
    )
    years = models.ManyToManyField(Year, related_name="weeks")

    @property
    def num_days(self):
        return self.days.count()

    def __str__(self):
        return "%s" % (self.week_number)

    class Meta:
        ordering = ["-week_number"]


class Day(models.Model):
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
        indexes = [models.Index(fields=["date"])]


class Hour(models.Model):
    day = models.ForeignKey(
        "Day", on_delete=models.CASCADE, related_name="hours", null=True, db_index=True
    )
    hour_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(23)], default=0
    )

    class Meta:
        ordering = ["-day__date", "-hour_number"]
        indexes = [models.Index(fields=["day", "hour_number"])]


class YearData(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="year_datas", null=True
    )
    year = models.ForeignKey(
        "Year", on_delete=models.CASCADE, related_name="year_datas", null=True
    )
    measurements = models.ManyToManyField("Measurement", related_name="year_datas")

    class Meta:
        ordering = ["-year__year_number"]
        indexes = [models.Index(fields=["year"])]


class MonthData(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="month_datas", null=True
    )
    month = models.ForeignKey(
        "Month", on_delete=models.CASCADE, related_name="month_datas", null=True
    )
    year = models.ForeignKey(
        "Year", on_delete=models.CASCADE, related_name="month_datas", null=True
    )
    measurements = models.ManyToManyField("Measurement", related_name="month_datas")

    class Meta:
        ordering = ["-year__year_number", "-month__month_number"]
        indexes = [models.Index(fields=["station", "month"])]


class WeekData(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="week_datas", null=True
    )
    week = models.ForeignKey(
        "Week", on_delete=models.CASCADE, related_name="week_datas", null=True
    )
    measurements = models.ManyToManyField("Measurement", related_name="week_datas")

    class Meta:
        ordering = ["-week__week_number"]
        indexes = [models.Index(fields=["station", "week"])]


class DayData(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="day_datas", null=True
    )
    day = models.ForeignKey(
        "Day", on_delete=models.CASCADE, related_name="day_datas", null=True
    )
    measurements = models.ManyToManyField("Measurement", related_name="day_datas")

    class Meta:
        ordering = ["-day__date"]
        indexes = [models.Index(fields=["station", "day"])]


# Hourly data for a day
class HourData(models.Model):
    station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="hour_datas", null=True
    )
    hour = models.ForeignKey(
        "Hour", on_delete=models.CASCADE, related_name="hour_datas", null=True
    )
    measurements = models.ManyToManyField("Measurement", related_name="hour_datas")

    class Meta:
        ordering = ["-hour__day__date", "-hour__hour_number"]
        indexes = [models.Index(fields=["station", "hour"])]
