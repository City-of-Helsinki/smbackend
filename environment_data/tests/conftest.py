import pytest
from dateutil import parser
from rest_framework.test import APIClient

from environment_data.constants import AIR_QUALITY, WEATHER_OBSERVATION
from environment_data.models import (
    Day,
    DayData,
    Hour,
    HourData,
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


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def stations(parameters):
    station = Station.objects.create(
        id=1, geo_id=42, name="Test", data_type=AIR_QUALITY, location="POINT(60.1 22.2)"
    )
    station.parameters.add(Parameter.objects.get(id=1))
    station.parameters.add(Parameter.objects.get(id=2))

    station = Station.objects.create(
        id=2,
        geo_id=43,
        name="Test2",
        data_type=WEATHER_OBSERVATION,
        location="POINT(60.1 22.2)",
    )
    station.parameters.add(Parameter.objects.get(id=1))
    return Station.objects.all()


@pytest.mark.django_db
@pytest.fixture
def measurements(parameters):
    Measurement.objects.create(id=1, parameter=Parameter.objects.get(id=1), value=1.5)
    return Measurement.objects.all()


@pytest.mark.django_db
@pytest.fixture
def parameters():
    Parameter.objects.create(id=1, name="AQINDEX_PT1H_avg")
    Parameter.objects.create(id=2, name="NO2_PT1H_avg")
    Parameter.objects.create(id=3, name="WS_PT1H_avg")

    return Parameter.objects.all()


@pytest.mark.django_db
@pytest.fixture
def years():
    Year.objects.create(id=1, year_number=2023)
    return Year.objects.all()


@pytest.mark.django_db
@pytest.fixture
def months(years):
    Month.objects.create(month_number=1, year=years[0])
    return Month.objects.all()


@pytest.mark.django_db
@pytest.fixture
def weeks(years):
    week = Week.objects.create(week_number=1)
    week.years.add(years[0])
    return Week.objects.all()


@pytest.mark.django_db
@pytest.fixture
def days(years, months, weeks):
    Day.objects.create(
        date=parser.parse("2023-01-01 00:00:00"),
        year=years[0],
        month=months[0],
        week=weeks[0],
    )
    return Day.objects.all()


@pytest.mark.django_db
@pytest.fixture
def hours(days):
    Hour.objects.create(day=days[0], hour_number=0)
    return Hour.objects.all()


@pytest.mark.django_db
@pytest.fixture
def year_datas(stations, years, measurements):
    year_data = YearData.objects.create(station=stations[0], year=years[0])
    year_data.measurements.add(measurements[0])
    return YearData.objects.all()


@pytest.mark.django_db
@pytest.fixture
def month_datas(stations, months, measurements):
    month_data = MonthData.objects.create(station=stations[0], month=months[0])
    month_data.measurements.add(measurements[0])
    return MonthData.objects.all()


@pytest.mark.django_db
@pytest.fixture
def week_datas(stations, weeks, measurements):
    week_data = WeekData.objects.create(station=stations[0], week=weeks[0])
    week_data.measurements.add(measurements[0])
    return WeekData.objects.all()


@pytest.mark.django_db
@pytest.fixture
def day_datas(stations, days, measurements):
    day_data = DayData.objects.create(station=stations[0], day=days[0])
    day_data.measurements.add(measurements[0])
    return DayData.objects.all()


@pytest.mark.django_db
@pytest.fixture
def hour_datas(stations, hours, measurements):
    hour_data = HourData.objects.create(station=stations[0], hour=hours[0])
    hour_data.measurements.add(measurements[0])
    return HourData.objects.all()
