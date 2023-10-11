from datetime import timedelta

import pytest
from rest_framework.reverse import reverse

from .constants import TEST_EC_STATION_NAME


@pytest.mark.django_db
def test_is_active(api_client, is_active_fixtures):
    url = reverse("eco_counter:stations-detail", args=[0])
    response = api_client.get(url)
    assert response.status_code == 200
    is_active = response.json()["is_active"]
    assert is_active["1"] is False
    assert is_active["7"] is False
    assert is_active["30"] is False
    assert is_active["365"] is False
    url = reverse("eco_counter:stations-detail", args=[1])
    response = api_client.get(url)
    assert response.status_code == 200
    is_active = response.json()["is_active"]
    assert is_active["1"] is True
    assert is_active["7"] is True
    assert is_active["30"] is True
    assert is_active["365"] is True
    url = reverse("eco_counter:stations-detail", args=[7])
    response = api_client.get(url)
    assert response.status_code == 200
    is_active = response.json()["is_active"]
    assert is_active["1"] is False
    assert is_active["7"] is True
    assert is_active["30"] is True
    assert is_active["365"] is True
    url = reverse("eco_counter:stations-detail", args=[30])
    response = api_client.get(url)
    assert response.status_code == 200
    is_active = response.json()["is_active"]
    assert is_active["1"] is False
    assert is_active["7"] is False
    assert is_active["30"] is True
    assert is_active["365"] is True


@pytest.mark.django_db
def test_hour_data(api_client, hour_data):
    url = reverse("eco_counter:hour_data-list")
    response = api_client.get(url)
    assert response.status_code == 200
    for i in range(24):
        assert response.json()["results"][0]["values_ak"][i] == hour_data.values_ak[i]
        assert response.json()["results"][0]["values_ap"][i] == hour_data.values_ap[i]


@pytest.mark.django_db
def test_day_data(
    api_client,
    day_datas,
):
    url = reverse("eco_counter:day_data-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    for i in range(7):
        # reverse order for day_datas as their order_by property is ascending
        assert (
            results[i]["day_info"]["station_name"] == day_datas[6 - i].day.station.name
        )
        assert results[i]["value_ak"] == day_datas[6 - i].value_ak
        assert results[i]["value_ap"] == day_datas[6 - i].value_ap
        assert results[i]["value_jk"] == day_datas[6 - i].value_jk
        assert results[i]["value_jp"] == day_datas[6 - i].value_jp


@pytest.mark.django_db
def test_get_day_data(api_client, day_datas, station_id, test_timestamp):
    url = reverse(
        "eco_counter:day_data-get-day-data"
    ) + "?station_id={}&date={}".format(station_id, test_timestamp + timedelta(days=3))
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["value_ak"] == day_datas[3].value_ak
    assert response.json()["value_ap"] == day_datas[3].value_ap
    assert response.json()["value_jk"] == day_datas[3].value_jk


@pytest.mark.django_db
def test_get_day_datas(api_client, day_datas, station_id, test_timestamp):
    url = reverse(
        "eco_counter:day_data-get-day-datas"
    ) + "?station_id={}&start_date={}&end_date={}".format(
        station_id, test_timestamp, test_timestamp + timedelta(days=3)
    )
    response = api_client.get(url)
    assert response.status_code == 200
    res_json = response.json()
    for i in range(4):
        assert res_json[i]["value_ak"] == day_datas[i].value_ak
        assert res_json[i]["value_ap"] == day_datas[i].value_ap
        assert res_json[i]["value_jp"] == day_datas[i].value_jp


@pytest.mark.django_db
def test_week_data(api_client, week_datas):
    url = reverse("eco_counter:week_data-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    for i in range(4):
        assert (
            results[i]["week_info"]["station_name"]
            == week_datas[3 - i].week.station.name
        )
        assert results[i]["value_ak"] == week_datas[3 - i].value_ak
        assert results[i]["value_ap"] == week_datas[3 - i].value_ap
        assert results[i]["value_jk"] == week_datas[3 - i].value_jk
        assert results[i]["value_jp"] == week_datas[3 - i].value_jp


@pytest.mark.django_db
def test_get_week_data(api_client, week_datas, station_id, test_timestamp):
    url = reverse(
        "eco_counter:week_data-get-week-data"
    ) + "?station_id={}&week_number={}&year_number={}".format(
        station_id, test_timestamp.strftime("%-V"), test_timestamp.year
    )
    response = api_client.get(url)
    assert response.json()["value_ak"] == week_datas[0].value_ak
    assert response.json()["value_ap"] == week_datas[0].value_ap
    assert response.json()["value_pk"] == week_datas[0].value_pk


@pytest.mark.django_db
def test_get_week_datas(api_client, week_datas, station_id, test_timestamp):
    end_week_number = test_timestamp + timedelta(weeks=4)
    url = reverse(
        "eco_counter:week_data-get-week-datas"
    ) + "?station_id={}&start_week_number={}&end_week_number={}&year_number={}".format(
        station_id,
        test_timestamp.strftime("%-V"),
        end_week_number.strftime("%-V"),
        test_timestamp.year,
    )
    response = api_client.get(url)
    assert response.status_code == 200
    res_json = response.json()
    for i in range(4):
        assert res_json[i]["value_ak"] == week_datas[i].value_ak
        assert res_json[i]["value_ap"] == week_datas[i].value_ap
        assert res_json[i]["value_jp"] == week_datas[i].value_jp


@pytest.mark.django_db
def test_month_data(api_client, month_datas):
    url = reverse("eco_counter:month_data-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    for i in range(4):
        assert (
            results[i]["month_info"]["station_name"]
            == month_datas[3 - i].month.station.name
        )
        # month_data is ordered ascedning
        assert results[i]["value_ak"] == month_datas[3 - i].value_ak
        assert results[i]["value_ap"] == month_datas[3 - i].value_ap
        assert results[i]["value_jk"] == month_datas[3 - i].value_jk
        assert results[i]["value_jp"] == month_datas[3 - i].value_jp


@pytest.mark.django_db
def test_get_month_data(api_client, month_datas, station_id, test_timestamp):
    url = reverse(
        "eco_counter:month_data-get-month-data"
    ) + "?station_id={}&month_number={}&year_number={}".format(
        station_id, test_timestamp.month, test_timestamp.year
    )
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["value_ak"] == month_datas[0].value_ak
    assert response.json()["value_ap"] == month_datas[0].value_ap
    assert response.json()["value_pk"] == month_datas[0].value_pk


@pytest.mark.django_db
def test_get_year_datas(api_client, year_datas, station_id, test_timestamp):
    end_year_number = test_timestamp.replace(year=test_timestamp.year + 1).year
    url = reverse(
        "eco_counter:year_data-get-year-datas"
    ) + "?station_id={}&start_year_number={}&end_year_number={}".format(
        station_id, test_timestamp.year, end_year_number
    )
    response = api_client.get(url)
    assert response.status_code == 200
    json_data = response.json()
    index = 0
    assert json_data[index]["year_info"]["year_number"] == 2020
    assert json_data[index]["value_ak"] == 42
    assert json_data[index]["value_ap"] == 43
    assert (
        json_data[index]["value_at"]
        == json_data[index]["value_ak"] + json_data[index]["value_ap"]
    )
    index = 1
    assert json_data[index]["year_info"]["year_number"] == 2021
    assert json_data[index]["value_ak"] == 43
    assert json_data[index]["value_ap"] == 44
    assert (
        json_data[index]["value_at"]
        == json_data[index]["value_ak"] + json_data[index]["value_ap"]
    )


@pytest.mark.django_db
def test_get_month_datas(api_client, month_datas, station_id, test_timestamp):
    url = reverse(
        "eco_counter:month_data-get-month-datas"
    ) + "?station_id={}&start_month_number={}&end_month_number={}&year_number={}".format(
        station_id, test_timestamp.month, test_timestamp.month + 4, test_timestamp.year
    )
    response = api_client.get(url)
    assert response.status_code == 200
    res_json = response.json()
    for i in range(4):
        assert res_json[i]["value_ak"] == month_datas[i].value_ak
        assert res_json[i]["value_ap"] == month_datas[i].value_ap
        assert res_json[i]["value_jp"] == month_datas[i].value_jp


@pytest.mark.django_db
def test_year_data(api_client, year_datas):
    url = reverse("eco_counter:year_data-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    for i in range(2):
        assert results[i]["value_ak"] == year_datas[1 - i].value_ak
        assert results[i]["value_ap"] == year_datas[1 - i].value_ap
        assert results[i]["value_jk"] == year_datas[1 - i].value_jk
        assert results[i]["value_jp"] == year_datas[1 - i].value_jp


@pytest.mark.django_db
def test_days(api_client, days, test_timestamp):
    url = reverse("eco_counter:days-list")
    response = api_client.get(url)
    assert response.status_code == 200
    # response is in ascending order
    day1 = response.json()["results"][0]
    day2 = response.json()["results"][6]
    assert day1["date"] == str(test_timestamp + timedelta(days=6))
    assert day1["weekday_number"] == 1  # 2020.1.7 is tuesday (0-6)
    assert day1["station_name"] == days[6].station.name
    assert day2["date"] == str(test_timestamp)
    assert day2["weekday_number"] == 2  # 2020.1.1 is wednesday


@pytest.mark.django_db
def test_weeks(api_client, weeks, test_timestamp):
    url = reverse("eco_counter:weeks-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    week1 = results[0]
    week2 = results[3]
    assert week1["week_number"] == 4
    assert week1["station_name"] == weeks[3].station.name
    assert week1["years"][0]["year_number"] == test_timestamp.year
    assert week2["week_number"] == 1


@pytest.mark.django_db
def test_months(api_client, months, test_timestamp):
    url = reverse("eco_counter:months-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    # response is in ascending order
    month1 = results[0]
    month2 = results[3]
    assert month1["month_number"] == 4
    assert month1["station_name"] == months[3].station.name
    assert month1["year_number"] == test_timestamp.year
    assert month2["month_number"] == 1
    assert month2["year_number"] == test_timestamp.year


@pytest.mark.django_db
def test_months_multiple_years(api_client, years, test_timestamp):
    url = reverse("eco_counter:years-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    # response is in ascending order
    year1 = results[0]
    year2 = results[1]
    assert year1["year_number"] == test_timestamp.year + 1
    assert year1["station_name"] == years[1].station.name
    assert year2["year_number"] == test_timestamp.year


@pytest.mark.django_db
def test_station(api_client, stations, year_datas, day_datas):
    url = reverse("eco_counter:stations-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["results"][0]["name"] == TEST_EC_STATION_NAME
    assert response.json()["results"][0]["sensor_types"] == ["at"]
    assert response.json()["results"][0]["data_until_date"] == "2020-01-07"
    assert response.json()["results"][0]["data_from_date"] == "2020-01-01"
    # Test retrieving station by data type
    url = reverse("eco_counter:stations-list") + "?data_type=a"
    response = api_client.get(url)
    assert response.json()["count"] == 1
    url = reverse("eco_counter:stations-list") + "?data_type=p"
    response = api_client.get(url)
    assert response.json()["count"] == 0
