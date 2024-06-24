from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from rest_framework.reverse import reverse

SITUATION_LIST_URL = reverse("exceptional_situations:situation-list")
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


@pytest.mark.django_db
def test_situations_list(api_client, situations, inactive_situations):
    response = api_client.get(SITUATION_LIST_URL)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {"count", "next", "previous", "results"}
    assert json_data["count"] == 3
    result_data = json_data["results"][0]
    assert result_data.keys() == {
        "id",
        "is_active",
        "start_time",
        "end_time",
        "situation_id",
        "release_time",
        "situation_type",
        "situation_type_str",
        "situation_sub_type_str",
        "announcements",
    }
    assert len(result_data["announcements"]) == 1
    announcement = result_data["announcements"][0]
    assert announcement.keys() == {
        "id",
        "title",
        "description",
        "start_time",
        "end_time",
        "additional_info",
        "location",
        "municipality_names",
    }
    location = announcement["location"]
    assert location.keys() == {"id", "location", "geometry", "details"}


@pytest.mark.django_db
def test_situation_retrieve(api_client, situations):
    response = api_client.get(
        reverse(
            "exceptional_situations:situation-detail", kwargs={"pk": situations[0].pk}
        )
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {
        "id",
        "is_active",
        "start_time",
        "end_time",
        "situation_id",
        "release_time",
        "situation_type",
        "situation_type_str",
        "situation_sub_type_str",
        "announcements",
    }
    assert json_data["id"] == situations[0].pk
    assert json_data["is_active"] is True


@pytest.mark.django_db
def test_situation_filter_by_start_time(api_client, situations):
    start_time = timezone.now()
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?start_time__gt={datetime.strftime(start_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 1
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?start_time__lt={datetime.strftime(start_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 1

    start_time = timezone.now() - timedelta(days=2)
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?start_time__gt={datetime.strftime(start_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 2
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?start_time__lt={datetime.strftime(start_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_situation_filter_by_end_time(api_client, situations):
    end_time = timezone.now()
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?end_time__gt={datetime.strftime(end_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 2
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?end_time__lt={datetime.strftime(end_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 0

    end_time = timezone.now() - timedelta(days=2)
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?end_time__gt={datetime.strftime(end_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 2
    response = api_client.get(
        SITUATION_LIST_URL
        + f"?end_time__lt={datetime.strftime(end_time, DATETIME_FORMAT)}"
    )
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_filter_by_municipalities(api_client, situations):
    response = api_client.get(SITUATION_LIST_URL + "?municipalities=raisio,lieto")
    assert response.json()["count"] == 2
    response = api_client.get(SITUATION_LIST_URL + "?municipalities=turku")
    assert response.json()["count"] == 1


@pytest.mark.django_db
def test_situation_types_list(api_client, situation_types):
    response = api_client.get(reverse("exceptional_situations:situation_type-list"))
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {"count", "next", "previous", "results"}
    assert json_data["count"] == situation_types.count()


@pytest.mark.django_db
def test_situation_types_retrieve(api_client, situation_types):
    response = api_client.get(
        reverse(
            "exceptional_situations:situation_type-detail",
            kwargs={"pk": situation_types[0].pk},
        )
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {"id", "type_name", "sub_type_name"}
    assert json_data["id"] == situation_types[0].pk


@pytest.mark.django_db
def test_announcement_list(api_client, announcements):
    response = api_client.get(
        reverse("exceptional_situations:situation_announcement-list")
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {"count", "next", "previous", "results"}
    assert json_data["count"] == announcements.count()
    result_data = json_data["results"][0]
    assert result_data.keys() == {
        "id",
        "title",
        "description",
        "start_time",
        "end_time",
        "additional_info",
        "location",
        "municipality_names",
    }
    location = result_data["location"]
    assert location.keys() == {"id", "location", "geometry", "details"}


@pytest.mark.django_db
def test_announcement_retrieve(api_client, announcements):
    response = api_client.get(
        reverse(
            "exceptional_situations:situation_announcement-detail",
            kwargs={"pk": announcements[0].pk},
        )
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {
        "id",
        "title",
        "description",
        "start_time",
        "end_time",
        "additional_info",
        "location",
        "municipality_names",
    }
    assert json_data["id"] == announcements[0].pk


@pytest.mark.django_db
def test_location_list(api_client, locations):
    response = api_client.get(reverse("exceptional_situations:situation_location-list"))
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {"count", "next", "previous", "results"}
    assert json_data["count"] == locations.count()
    result_data = json_data["results"][0]
    assert result_data.keys() == {"id", "location", "geometry", "details"}


@pytest.mark.django_db
def test_location_retrieve(api_client, locations):
    response = api_client.get(
        reverse(
            "exceptional_situations:situation_location-detail",
            kwargs={"pk": locations[0].pk},
        )
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.keys() == {"id", "location", "geometry", "details"}
    assert json_data["id"] == locations[0].pk
