from datetime import timedelta

import dateutil.parser
import pytest
from dateutil.relativedelta import relativedelta
from rest_framework.test import APIClient

from eco_counter.constants import ECO_COUNTER, LAM_COUNTER, TRAFFIC_COUNTER
from eco_counter.models import (
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

from .constants import TEST_EC_STATION_NAME, TEST_LC_STATION_NAME, TEST_TC_STATION_NAME

TEST_TIMESTAMP = dateutil.parser.parse("2020-01-01 00:00:00")


@pytest.fixture
def test_timestamp():
    return TEST_TIMESTAMP.date()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def stations():
    stations = []
    stations.append(
        Station.objects.create(
            name=TEST_EC_STATION_NAME,
            location="POINT(60.4487578455581 22.269454227550053)",
            csv_data_source=ECO_COUNTER,
        )
    )
    stations.append(
        Station.objects.create(
            name=TEST_TC_STATION_NAME,
            location="POINT(60.4487578455581 22.269454227550053)",
            csv_data_source=TRAFFIC_COUNTER,
        )
    )
    stations.append(
        Station.objects.create(
            name=TEST_LC_STATION_NAME,
            location="POINT(60.4487578455581 22.269454227550053)",
            csv_data_source=LAM_COUNTER,
        )
    )

    return stations


@pytest.mark.django_db
@pytest.fixture
def station_id():
    return Station.objects.get(name=TEST_EC_STATION_NAME).id


@pytest.mark.django_db
@pytest.fixture
def years(stations):
    years = []
    for i in range(2):
        year = Year.objects.create(
            station=stations[0], year_number=TEST_TIMESTAMP.year + i
        )
        years.append(year)
    return years


@pytest.mark.django_db
@pytest.fixture
def months(stations, years):
    months = []
    for i in range(4):
        timestamp = TEST_TIMESTAMP + relativedelta(months=i)
        month_number = int(timestamp.month)
        month = Month.objects.create(
            station=stations[0], month_number=month_number, year=years[0]
        )
        months.append(month)
    return months


@pytest.mark.django_db
@pytest.fixture
def weeks(stations, years):
    weeks = []
    for i in range(4):
        timestamp = TEST_TIMESTAMP + timedelta(weeks=i)
        week_number = int(timestamp.strftime("%-V"))
        week = Week.objects.create(station=stations[0], week_number=week_number)
        week.years.add(years[0])
        weeks.append(week)
    return weeks


@pytest.mark.django_db
@pytest.fixture
def days(stations, years, months, weeks):
    days = []
    for i in range(7):
        timestamp = TEST_TIMESTAMP + timedelta(days=i)
        day = Day.objects.create(
            station=stations[0],
            date=timestamp,
            weekday_number=timestamp.weekday(),
            week=weeks[0],
            month=months[0],
            year=years[0],
        )
        days.append(day)
    return days


@pytest.mark.django_db
@pytest.fixture
def hour_data(stations, days):
    hour_data = HourData.objects.create(
        station=stations[0],
        day=days[0],
    )
    hour_data.values_ak = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
    ]
    hour_data.values_ap = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
    ]
    hour_data.save()
    return hour_data


@pytest.mark.django_db
@pytest.fixture
def day_datas(stations, days):
    day_datas = []
    for i in range(7):
        day_data = DayData.objects.create(station=stations[0], day=days[i])
        day_data.value_ak = 5 + i
        day_data.value_ap = 6 + i
        day_data.save()
        day_datas.append(day_data)
    return day_datas


@pytest.mark.django_db
@pytest.fixture
def week_datas(stations, weeks):
    week_datas = []
    for i in range(4):
        week_data = WeekData.objects.create(station=stations[0], week=weeks[i])
        week_data.value_ak = 10 + i
        week_data.value_ap = 20 + i
        week_data.save()
        week_datas.append(week_data)
    return week_datas


@pytest.mark.django_db
@pytest.fixture
def month_datas(stations, months):
    month_datas = []
    for i in range(4):
        month_data = MonthData.objects.create(station=stations[0], month=months[i])
        month_data.value_ak = 10 + i
        month_data.value_ap = 20 + i
        month_data.save()
        month_datas.append(month_data)
    return month_datas


@pytest.mark.django_db
@pytest.fixture
def year_datas(stations, years):
    year_datas = []
    for i in range(2):
        year_data = YearData.objects.create(station=stations[0], year=years[i])
        year_data.value_ak = 42 + i
        year_data.value_ap = 43 + i
        year_data.value_at = year_data.value_ak + year_data.value_ap
        year_data.save()
        year_datas.append(year_data)
    return year_datas
