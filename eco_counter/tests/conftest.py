from datetime import date, timedelta

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
            sensor_types=["at"],
            data_until_date="2020-01-07",
            data_from_date="2020-01-01",
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
def years():
    years = []
    for i in range(2):
        year = Year.objects.create(year_number=TEST_TIMESTAMP.year + i)
        years.append(year)
    return years


@pytest.mark.django_db
@pytest.fixture
def months(years):
    months = []
    for i in range(4):
        timestamp = TEST_TIMESTAMP + relativedelta(months=i)
        month_number = int(timestamp.month)
        month = Month.objects.create(month_number=month_number, year=years[0])
        months.append(month)
    return months


@pytest.mark.django_db
@pytest.fixture
def weeks(years):
    weeks = []
    for i in range(4):
        timestamp = TEST_TIMESTAMP + timedelta(weeks=i)
        week_number = int(timestamp.strftime("%-V"))
        week = Week.objects.create(week_number=week_number)
        week.years.add(years[0])
        weeks.append(week)
    return weeks


@pytest.mark.django_db
@pytest.fixture
def days(years, months, weeks):
    days = []
    for i in range(7):
        timestamp = TEST_TIMESTAMP + timedelta(days=i)
        day = Day.objects.create(
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
    hour_data.values_ak = [v for v in range(1, 25)]
    hour_data.values_ap = [v for v in range(1, 25)]
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
        day_data.value_at = day_data.value_ak + day_data.value_ap
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


@pytest.mark.django_db
@pytest.fixture
def is_active_fixtures():
    station0 = Station.objects.create(
        id=0,
        name="Station with 0 day of data",
        location="POINT(0 0)",
        csv_data_source=LAM_COUNTER,
        is_active={"1": False, "7": False, "30": False, "365": False},
    )
    station1 = Station.objects.create(
        id=1,
        name="Station with 1 day of data",
        location="POINT(0 0)",
        csv_data_source=LAM_COUNTER,
        is_active={"1": True, "7": True, "30": True, "365": True},
    )
    station7 = Station.objects.create(
        id=7,
        name="Station with 7 days of data",
        location="POINT(0 0)",
        csv_data_source=LAM_COUNTER,
        is_active={"1": False, "7": True, "30": True, "365": True},
    )
    station30 = Station.objects.create(
        id=30,
        name="Station with 30 days of data",
        location="POINT(0 0)",
        csv_data_source=LAM_COUNTER,
        is_active={"1": False, "7": False, "30": True, "365": True},
    )
    start_date = date.today()
    current_date = start_date
    days_counter = 0
    day_counts = [0, 1, 7, 30]
    stations = [station0, station1, station7, station30]
    while current_date >= start_date - timedelta(days=32):
        for i, station in enumerate(stations):
            days = day_counts[i]
            day = Day.objects.create(date=current_date)
            day_data = DayData.objects.create(station=station, day=day)
            if i > 0:
                start_day = day_counts[i - 1]
            else:
                start_day = 10000

            if days > days_counter & days_counter >= start_day:
                day_data.value_at = 1
                day_data.value_pt = 1
                day_data.value_jt = 1
                day_data.value_bt = 1
                day_data.save()
            else:
                day_data.value_at = 0
                day_data.value_pt = 0
                day_data.value_jt = 0
                day_data.value_bt = 0
                day_data.save()

        current_date -= timedelta(days=1)
        days_counter += 1
    return Station.objects.all(), Day.objects.all(), DayData.objects.all()
