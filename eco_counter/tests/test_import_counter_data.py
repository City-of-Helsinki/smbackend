"""
To run test: pytest -m pytest -m test_import_counter_data
Test has been marked with the test_import_counter_data marker and is not
executed by default. The reason is that the tests are very slow
and only needed if changes are made to the importer.
The main purpose of these tests are to verify that the importer
imports and calculates the data correctly.
"""
import calendar
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import dateutil.parser
import pytest
from django.core.management import call_command

from eco_counter.constants import (
    ECO_COUNTER,
    LAM_COUNTER,
    TELRAAM_COUNTER,
    TRAFFIC_COUNTER,
)
from eco_counter.models import (
    Day,
    DayData,
    HourData,
    ImportState,
    Month,
    MonthData,
    Station,
    Week,
    WeekData,
    Year,
    YearData,
)
from eco_counter.tests.utils import get_telraam_data_frames_test_fixture

from .constants import TEST_EC_STATION_NAME, TEST_LC_STATION_NAME, TEST_TC_STATION_NAME


def import_command(*args, **kwargs):
    out = StringIO()
    call_command(
        "import_counter_data",
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
    return out.getvalue()


@pytest.mark.django_db
@patch("eco_counter.management.commands.utils.get_telraam_data_frames")
def test_import_telraam(get_telraam_data_frames_mock):
    from eco_counter.management.commands.import_counter_data import import_data

    start_time = dateutil.parser.parse("2023-09-01T00:00")
    ImportState.objects.create(
        current_year_number=start_time.year,
        current_month_number=start_time.month,
        current_day_number=start_time.day,
        csv_data_source=TELRAAM_COUNTER,
    )
    num_days_per_location = 2
    get_telraam_data_frames_mock.return_value = get_telraam_data_frames_test_fixture(
        start_time,
        num_cameras=2,
        num_locations=3,
        num_days_per_location=num_days_per_location,
    )
    import_data([TELRAAM_COUNTER])
    stations_qs = Station.objects.all()
    # num_stations * nul_locations, as for every location a station is created
    assert stations_qs.count() == 6
    assert DayData.objects.count() == 12
    assert HourData.objects.count() == 12
    assert stations_qs.first().location.wkt == "POINT (2032 2032)"
    assert Year.objects.count() == stations_qs.count()
    import_state_qs = ImportState.objects.filter(csv_data_source=TELRAAM_COUNTER)
    assert import_state_qs.count() == 1
    import_state = import_state_qs.first()
    assert import_state.current_year_number == 2023
    assert import_state.current_month_number == 9
    assert import_state.current_day_number == 2
    # 12
    assert Day.objects.count() == stations_qs.count() * num_days_per_location
    # Test that duplicates are not created
    get_telraam_data_frames_mock.return_value = get_telraam_data_frames_test_fixture(
        start_time,
        num_cameras=2,
        num_locations=3,
        num_days_per_location=num_days_per_location,
    )
    import_data([TELRAAM_COUNTER])
    assert stations_qs.count() == 6
    assert Year.objects.count() == stations_qs.count()
    assert Day.objects.count() == stations_qs.count() * num_days_per_location
    assert DayData.objects.count() == 12
    assert HourData.objects.count() == 12
    # Test new locations, adds 2 stations
    new_start_time = start_time + timedelta(days=2)
    get_telraam_data_frames_mock.return_value = get_telraam_data_frames_test_fixture(
        new_start_time,
        num_cameras=2,
        num_locations=1,
        num_days_per_location=num_days_per_location,
    )
    import_data([TELRAAM_COUNTER])
    stations_qs = Station.objects.all()
    assert stations_qs.count() == 8
    assert Year.objects.count() == stations_qs.count()
    assert Day.objects.count() == 16
    # Test adding camera
    get_telraam_data_frames_mock.return_value = get_telraam_data_frames_test_fixture(
        new_start_time,
        num_cameras=3,
        num_locations=1,
        num_days_per_location=num_days_per_location,
    )
    import_data([TELRAAM_COUNTER])
    stations_qs = Station.objects.all()
    assert stations_qs.count() == 9
    assert Year.objects.count() == stations_qs.count()
    # Test data related to first station
    station = Station.objects.filter(station_id="0").first()
    year_data = YearData.objects.get(station=station)
    assert year_data.value_ak == 24 * num_days_per_location
    assert year_data.value_ap == 24 * num_days_per_location
    assert year_data.value_at == 24 * num_days_per_location * 2
    assert year_data.value_pk == 24 * num_days_per_location
    assert year_data.value_pp == 24 * num_days_per_location
    assert year_data.value_pt == 24 * num_days_per_location * 2
    assert MonthData.objects.count() == stations_qs.count() * Year.objects.count()
    assert Month.objects.count() == stations_qs.count() * Year.objects.count()
    assert (
        MonthData.objects.get(station=station, month=Month.objects.first()).value_at
        == 24 * num_days_per_location * 2
    )
    # 1.9.2023 is a friday, 9 stations has data for 1-3.9(week 34) and 3 stations has data for
    # 4.5 (week 36)
    assert WeekData.objects.count() == 12
    assert Week.objects.count() == 12
    # location*camera = 6 * num_days_per_location + cameras * num_days_per_location
    DayData.objects.count() == 6 * 2 + 3 * 2
    Day.objects.count() == 6 * 2 + 3 * 2

    # Three locations for two cameras
    assert Day.objects.filter(date__day=1).count() == 6
    # One location for Three cameras
    assert Day.objects.filter(date__day=4).count() == 3
    assert DayData.objects.first().value_at == 48
    assert DayData.objects.first().value_ap == 24
    assert DayData.objects.first().value_ak == 24
    HourData.objects.count() == 18
    for hour_data in HourData.objects.all():
        hour_data.values_ak == [1 for x in range(24)]
        hour_data.values_at == [2 for x in range(24)]


@pytest.mark.test_import_counter_data
@pytest.mark.django_db
def test_import_eco_counter_data(stations):
    """
    In test data, for every 15min the value 1 is set, so the sum for an hour is 4.
    For a day the sum is 96(24*4) and for a week 682(96*7).
    The month sum depends on how  many days the month has,~3000
    1.1.2020 is used as the starting point.
    """

    start_time = dateutil.parser.parse("2020-01-01T00:00")
    end_time = dateutil.parser.parse("2020-02-29T23:45")
    import_command(test_counter=(ECO_COUNTER, start_time, end_time))
    num_ec_stations = Station.objects.filter(csv_data_source=ECO_COUNTER).count()
    assert Station.objects.get(name=TEST_EC_STATION_NAME)
    # Test hourly data
    hour_data = HourData.objects.get(
        station__name=TEST_EC_STATION_NAME, day__date=start_time
    )
    res = [4 for x in range(24)]
    res_tot = [8 for x in range(24)]
    assert hour_data.values_ap == res
    assert hour_data.values_ak == res
    assert hour_data.values_at == res_tot
    assert hour_data.values_pp == res
    assert hour_data.values_pk == res
    assert hour_data.values_pt == res_tot
    assert hour_data.values_jk == res
    assert hour_data.values_jp == res
    assert hour_data.values_jt == res_tot
    # Test day data
    day = Day.objects.get(date=start_time, station__name=TEST_EC_STATION_NAME)
    assert day.weekday_number == 2  # First day in 2020 in is wednesday
    day_data = DayData.objects.get(
        day__date=start_time, station__name=TEST_EC_STATION_NAME
    )
    assert day_data.value_jp == 96
    day_data = DayData.objects.filter(
        day__week__week_number=2, station__name=TEST_EC_STATION_NAME
    )[0]
    assert day_data.value_jt == 96 * 2
    day = Day.objects.get(
        date=dateutil.parser.parse("2020-01-06T00:00"),
        station__name=TEST_EC_STATION_NAME,
    )
    assert day.weekday_number == 0  # First day in week 2 in 2020 is monday

    # Test week data
    week_data = WeekData.objects.filter(
        week__week_number=1, station__name=TEST_EC_STATION_NAME
    )[0]
    week = Week.objects.filter(week_number=1)[0]
    # first week of 2020 has only 5 days, thus it is the start of the import
    assert week.days.count() == 5
    assert week_data.value_jp == 480  # 5*96
    week_data = WeekData.objects.filter(
        week__week_number=2, station__name=TEST_EC_STATION_NAME
    )[0]
    week = Week.objects.filter(week_number=2)[0]
    assert week.days.count() == 7  # second week of 2020 7 days.
    assert week_data.value_jp == 672  # 96*7
    assert week_data.value_jk == 672  # 96*7
    assert week_data.value_jt == 672 * 2  # 96*7
    assert Week.objects.filter(week_number=2).count() == num_ec_stations
    assert WeekData.objects.filter(week__week_number=2).count() == num_ec_stations
    # Test month data
    month = Month.objects.get(
        month_number=1, year__year_number=2020, station__name=TEST_EC_STATION_NAME
    )
    num_month_days = month.days.count()
    jan_month_days = calendar.monthrange(month.year.year_number, month.month_number)[1]
    assert num_month_days == jan_month_days
    month_data = MonthData.objects.get(month=month)
    assert month_data.value_pp == jan_month_days * 96
    assert month_data.value_pk == jan_month_days * 96
    assert month_data.value_pt == jan_month_days * 96 * 2
    month = Month.objects.get(
        month_number=2, year__year_number=2020, station__name=TEST_EC_STATION_NAME
    )
    num_month_days = month.days.count()
    feb_month_days = calendar.monthrange(month.year.year_number, month.month_number)[1]
    assert num_month_days == feb_month_days
    month_data = MonthData.objects.get(month=month)
    assert month_data.value_jp == feb_month_days * 96
    assert month_data.value_jk == feb_month_days * 96
    assert month_data.value_jt == feb_month_days * 96 * 2
    # test that number of days match
    assert (
        Day.objects.filter(station__name=TEST_EC_STATION_NAME).count()
        == jan_month_days + feb_month_days
    )
    year_data = YearData.objects.get(
        station__name=TEST_EC_STATION_NAME, year__year_number=2020
    )
    assert year_data.value_jp == jan_month_days * 96 + feb_month_days * 96
    assert Year.objects.get(station__name=TEST_EC_STATION_NAME, year_number=2020)
    # test state
    state = ImportState.objects.get(csv_data_source=ECO_COUNTER)
    assert state.current_month_number == 2
    assert state.current_year_number == 2020
    week = Week.objects.filter(week_number=5)[0]
    assert week.days.count() == 7
    # test incremental importing
    start_time = dateutil.parser.parse("2020-02-01T00:00")
    end_time = dateutil.parser.parse("2020-03-31T23:45")
    import_command(test_counter=(ECO_COUNTER, start_time, end_time))
    # test that state is updated
    state = ImportState.objects.get(csv_data_source=ECO_COUNTER)
    assert state.current_month_number == 3
    assert state.current_year_number == 2020
    # test that number of days in weeks remains intact
    week = Week.objects.filter(week_number=5)[0]
    assert week.days.count() == 7
    week = Week.objects.filter(week_number=6)[0]
    assert week.days.count() == 7
    # Test that we do not get multiple weeks
    assert Week.objects.filter(week_number=6).count() == num_ec_stations
    assert WeekData.objects.filter(week__week_number=6).count() == num_ec_stations
    day_data = DayData.objects.filter(
        day__week__week_number=10, station__name=TEST_EC_STATION_NAME
    )[0]
    assert day_data.value_jt == 96 * 2
    # Test week in previous month
    week_data = WeekData.objects.get(
        week__week_number=8, station__name=TEST_EC_STATION_NAME
    )
    week = Week.objects.get(week_number=8, station__name=TEST_EC_STATION_NAME)
    assert week.days.count() == 7
    assert week_data.value_jp == 672
    # Test starting month
    assert num_month_days == feb_month_days
    month_data = MonthData.objects.get(month=month)
    assert month_data.value_jp == feb_month_days * 96
    # Test new month
    month = Month.objects.get(
        month_number=3, year__year_number=2020, station__name=TEST_EC_STATION_NAME
    )
    num_month_days = month.days.count()
    mar_month_days = calendar.monthrange(month.year.year_number, month.month_number)[1]
    assert num_month_days == mar_month_days
    month_data = MonthData.objects.get(month=month)
    assert month_data.value_jp == mar_month_days * 96
    year_data = YearData.objects.get(
        year__year_number=2020, station__name=TEST_EC_STATION_NAME
    )
    assert year_data.value_jp == (
        jan_month_days * 96 + feb_month_days * 96 + mar_month_days * 96
    )
    # Test day when clock is changed to "summer time", i.e. one hour forward
    day = Day.objects.get(
        date=dateutil.parser.parse("2020-03-29T00:00"),
        station__name=TEST_EC_STATION_NAME,
    )
    assert year_data.value_pp == (
        jan_month_days * 96 + feb_month_days * 96 + mar_month_days * 96
    )
    # Test new year and daylight saving change to "winter time".
    start_time = dateutil.parser.parse("2021-10-01T00:00")
    end_time = dateutil.parser.parse("2021-10-31T23:45")
    import_command(test_counter=(ECO_COUNTER, start_time, end_time))
    # Test that year 2020 instance still exists.
    assert Year.objects.get(station__name=TEST_EC_STATION_NAME, year_number=2020)
    # Test new year instance is created.
    assert Year.objects.get(station__name=TEST_EC_STATION_NAME, year_number=2021)

    week_data = WeekData.objects.get(
        week__week_number=39,
        week__years__year_number=2021,
        station__name=TEST_EC_STATION_NAME,
    )
    week = Week.objects.get(
        week_number=39, years__year_number=2021, station__name=TEST_EC_STATION_NAME
    )
    assert week.days.count() == 3
    # week 39 in 2021 has only 3 days in October, the rest 4 days are in September.
    assert week_data.value_jp == 288  # 3*96
    week_data = WeekData.objects.get(
        week__week_number=40, station__name=TEST_EC_STATION_NAME
    )
    week = Week.objects.get(week_number=40, station__name=TEST_EC_STATION_NAME)
    assert week.days.count() == 7  # week 36 in 2021 has 7 days.
    assert week_data.value_jp == 672  # 96*7
    month = Month.objects.get(
        month_number=10, year__year_number=2021, station__name=TEST_EC_STATION_NAME
    )
    num_month_days = month.days.count()
    oct_month_days = calendar.monthrange(month.year.year_number, month.month_number)[1]
    assert num_month_days == oct_month_days
    month_data = MonthData.objects.get(month=month)
    assert month_data.value_jp == oct_month_days * 96
    # Test day when clock is changed to "winter time", i.e. backwards
    day = Day.objects.get(
        date=dateutil.parser.parse("2021-10-29T00:00"),
        station__name=TEST_EC_STATION_NAME,
    )
    # Test the day has 24hours stored even though in reality it hs 25hours.
    # assert len(HourData.objects.get(day_id=day.id).values_ak) == 24
    year_data = YearData.objects.get(
        year__year_number=2021, station__name=TEST_EC_STATION_NAME
    )
    assert year_data.value_pp == oct_month_days * 96
    # verify that previous year is intact
    year_data = YearData.objects.get(
        year__year_number=2020, station__name=TEST_EC_STATION_NAME
    )

    # test that state is updated
    state = ImportState.objects.get(csv_data_source=ECO_COUNTER)
    assert state.current_month_number == 10
    assert state.current_year_number == 2021
    # test year change and week 53
    # First set state to correct year, otherwise the importer will create duplicate years.
    # As the year is set to 2021 in previous test.
    state = ImportState.objects.get(csv_data_source=ECO_COUNTER)
    state.current_year_number = 2020
    state.save()
    start_time = dateutil.parser.parse("2020-12-26T00:00")
    end_time = dateutil.parser.parse("2021-01-17T23:45")
    import_command(test_counter=(ECO_COUNTER, start_time, end_time))
    weeks = Week.objects.filter(week_number=53, years__year_number=2020)
    assert len(weeks) == num_ec_stations
    # 4 days in 2020
    assert weeks[0].days.count() == 4
    weeks = Week.objects.filter(week_number=53, years__year_number=2021)
    assert len(weeks) == num_ec_stations
    assert weeks[0].days.count() == 3
    weeks = Week.objects.filter(week_number=1, years__year_number=2021)
    assert len(weeks) == num_ec_stations
    assert weeks[0].days.count() == 7
    weeks = Week.objects.filter(week_number=2, years__year_number=2021)
    assert len(weeks) == num_ec_stations
    assert weeks[0].days.count() == 7
    # Test that exacly one year object is created for every station in 2020
    assert Year.objects.filter(year_number=2020).count() == num_ec_stations


@pytest.mark.test_import_counter_data
@pytest.mark.django_db
def test_import_traffic_counter_data(stations):
    # Test importing of Traffic Counter
    start_time = dateutil.parser.parse("2020-01-01T00:00")
    end_time = dateutil.parser.parse("2020-02-29T23:45")
    import_command(test_counter=(TRAFFIC_COUNTER, start_time, end_time))
    num_tc_stations = Station.objects.filter(csv_data_source=TRAFFIC_COUNTER).count()
    state = ImportState.objects.get(csv_data_source=TRAFFIC_COUNTER)
    assert state.current_year_number == 2020
    assert state.current_month_number == 2
    hour_data = HourData.objects.get(
        station__name=TEST_TC_STATION_NAME, day__date=start_time
    )
    res = [4 for x in range(24)]
    res_tot = [8 for x in range(24)]
    assert hour_data.values_ak == res
    assert hour_data.values_ap == res
    assert hour_data.values_at == res_tot
    assert hour_data.values_pk == res
    assert hour_data.values_pp == res
    assert hour_data.values_pt == res_tot
    assert hour_data.values_jk == res
    assert hour_data.values_jp == res
    assert hour_data.values_jt == res_tot
    assert hour_data.values_bk == res
    assert hour_data.values_bp == res
    assert hour_data.values_bt == res_tot

    # Test traffic counter day data
    day = Day.objects.get(date=start_time, station__name=TEST_TC_STATION_NAME)
    assert day.weekday_number == 2  # First day in 2020 in is wednesday
    day_data = DayData.objects.get(
        day__date=start_time, station__name=TEST_TC_STATION_NAME
    )
    assert day_data.value_bp == 96
    day_data = DayData.objects.filter(
        day__week__week_number=2, station__name=TEST_TC_STATION_NAME
    )[0]
    assert day_data.value_bt == 96 * 2
    day = Day.objects.get(
        date=dateutil.parser.parse("2020-02-06T00:00"),
        station__name=TEST_TC_STATION_NAME,
    )
    assert day.weekday_number == 3  # Second day in week 2 in 2020 is thursday
    week_data = WeekData.objects.get(
        week__week_number=3, station__name=TEST_TC_STATION_NAME
    )
    week = Week.objects.filter(week_number=3)[0]
    assert week.days.count() == 7  # third week of 2020 7 days.
    assert week_data.value_bp == 672  # 96*7
    assert week_data.value_bk == 672  # 96*7
    assert week_data.value_bt == 672 * 2
    # Test traffic counter month data
    feb_month = Month.objects.get(
        station__name=TEST_TC_STATION_NAME, month_number=2, year__year_number=2020
    )
    num_month_days = feb_month.days.count()
    feb_month_days = calendar.monthrange(
        feb_month.year.year_number, feb_month.month_number
    )[1]
    assert num_month_days == feb_month_days
    month_data = MonthData.objects.get(month=feb_month)
    assert month_data.value_pp == feb_month_days * 96
    assert month_data.value_pk == feb_month_days * 96
    assert month_data.value_pt == feb_month_days * 96 * 2
    # Test traffic counter year data
    jan_month = Month.objects.get(
        station__name=TEST_TC_STATION_NAME, month_number=1, year__year_number=2020
    )
    jan_month_days = calendar.monthrange(
        jan_month.year.year_number, jan_month.month_number
    )[1]
    year_data = YearData.objects.get(
        station__name=TEST_TC_STATION_NAME, year__year_number=2020
    )
    assert year_data.value_bk == (jan_month_days + feb_month_days) * 24 * 4
    assert year_data.value_bp == (jan_month_days + feb_month_days) * 24 * 4
    assert year_data.value_bt == (jan_month_days + feb_month_days) * 24 * 4 * 2
    assert Year.objects.filter(year_number=2020).count() == num_tc_stations


@pytest.mark.test_import_counter_data
@pytest.mark.django_db
def test_import_lam_counter_data(stations):
    # Test lam counter data and year change
    start_time = dateutil.parser.parse("2019-12-01T00:00")
    end_time = dateutil.parser.parse("2020-01-31T23:45")
    import_command(test_counter=(LAM_COUNTER, start_time, end_time))
    num_lc_stations = Station.objects.filter(csv_data_source=LAM_COUNTER).count()
    state = ImportState.objects.get(csv_data_source=LAM_COUNTER)
    assert state.current_year_number == 2020
    assert state.current_month_number == 1
    test_station = Station.objects.get(name=TEST_LC_STATION_NAME)
    assert test_station
    hour_data = HourData.objects.get(
        station__name=TEST_LC_STATION_NAME, day__date=start_time
    )
    res = [4 for x in range(24)]
    res_tot = [8 for x in range(24)]
    assert hour_data.values_ak == res
    assert hour_data.values_ap == res
    assert hour_data.values_at == res_tot
    assert hour_data.values_pk == res
    assert hour_data.values_pp == res
    assert hour_data.values_pt == res_tot
    assert hour_data.values_jk == res
    assert hour_data.values_jp == res
    assert hour_data.values_jt == res_tot
    assert hour_data.values_bk == res
    assert hour_data.values_bp == res
    assert hour_data.values_bt == res_tot
    # 2019 December 2019 has 6 weeks(48,49,50,51,52 and 1) and January 2020 has 5 week = 11 weeks
    assert Week.objects.filter(station__name=TEST_LC_STATION_NAME).count() == 11
    # 5 days of week 5 in 2020 is imported, e.g. 4*24*5 = 480
    assert (
        WeekData.objects.filter(station__name=TEST_LC_STATION_NAME, week__week_number=5)
        .first()
        .value_ak
        == 480
    )
    # Test lam counter month data
    dec_month = Month.objects.get(
        station__name=TEST_LC_STATION_NAME, month_number=12, year__year_number=2019
    )
    jan_month = Month.objects.get(
        station__name=TEST_LC_STATION_NAME, month_number=1, year__year_number=2020
    )
    jan_month_days = calendar.monthrange(
        jan_month.year.year_number, jan_month.month_number
    )[1]
    dec_month_days = calendar.monthrange(
        dec_month.year.year_number, dec_month.month_number
    )[1]
    assert dec_month_days == dec_month.days.count()
    assert jan_month_days == jan_month.days.count()
    month_data = MonthData.objects.get(month=dec_month)
    assert month_data.value_pp == dec_month_days * 96
    assert month_data.value_pk == dec_month_days * 96
    assert month_data.value_pt == dec_month_days * 96 * 2

    month_data = MonthData.objects.get(month=jan_month)
    assert month_data.value_pp == jan_month_days * 96
    assert month_data.value_pk == jan_month_days * 96
    assert month_data.value_pt == jan_month_days * 96 * 2
    # Test lam counter year data
    year_data = YearData.objects.get(
        station__name=TEST_LC_STATION_NAME, year__year_number=2019
    )
    assert year_data.value_ak == jan_month_days * 24 * 4
    assert year_data.value_ap == jan_month_days * 24 * 4
    assert year_data.value_at == jan_month_days * 24 * 4 * 2
    year_data = YearData.objects.get(
        station__name=TEST_LC_STATION_NAME, year__year_number=2020
    )
    assert year_data.value_bk == dec_month_days * 24 * 4
    assert year_data.value_ap == dec_month_days * 24 * 4
    assert year_data.value_at == dec_month_days * 24 * 4 * 2
    # Test that only one month has been created for years 2019 and 2020
    assert (
        YearData.objects.filter(
            station__name=TEST_LC_STATION_NAME, year__year_number=2019
        ).count()
        == 1
    )
    assert (
        YearData.objects.filter(
            station__name=TEST_LC_STATION_NAME, year__year_number=2020
        ).count()
        == 1
    )
    assert Year.objects.filter(year_number=2020).count() == num_lc_stations
