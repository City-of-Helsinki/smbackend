import pytest
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from services.models import Announcement, ErrorMessage, Unit, UnitEntrance
from services.tests.utils import get

PICTURE_URL = "https://localhost/kuva.jpg"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def unit_entrance(unit):
    return UnitEntrance.objects.create(
        id=1,
        name="entrance",
        last_modified_time=timezone.now(),
        unit=unit,
        picture_url=PICTURE_URL,
    )


@pytest.fixture
def unit():
    return Unit.objects.create(
        id=1, last_modified_time=timezone.now(), public=True, picture_url=PICTURE_URL
    )


@pytest.mark.parametrize(
    "rewrite_enabled, expected_unit_picture_url, expected_unit_entrance_picture_url",
    [
        [False, PICTURE_URL, PICTURE_URL],
        [
            True,
            "http://testserver/v2/unit/1/picture/",
            "http://testserver/v2/unit_entrance/1/picture/",
        ],
    ],
)
@pytest.mark.django_db
def test_unit_and_unit_entrance_picture_url_rewrite(
    api_client,
    unit,
    unit_entrance,
    settings,
    rewrite_enabled,
    expected_unit_picture_url,
    expected_unit_entrance_picture_url,
):
    settings.PICTURE_URL_REWRITE_ENABLED = rewrite_enabled

    # Test list endpoints
    response = get(api_client, reverse("unit-list"))
    unit_response = response.data["results"][0]
    assert unit_response["picture_url"] == expected_unit_picture_url
    assert (
        unit_response["entrances"][0]["picture_url"]
        == expected_unit_entrance_picture_url
    )

    response = get(api_client, reverse("unitentrance-list"))
    assert (
        response.data["results"][0]["picture_url"] == expected_unit_entrance_picture_url
    )

    # Test detail endpoints
    response = get(api_client, reverse("unit-detail", kwargs={"pk": unit.id}))
    assert response.data["picture_url"] == expected_unit_picture_url
    assert (
        response.data["entrances"][0]["picture_url"]
        == expected_unit_entrance_picture_url
    )

    response = get(
        api_client, reverse("unitentrance-detail", kwargs={"pk": unit_entrance.id})
    )
    assert response.data["picture_url"] == expected_unit_entrance_picture_url

    # Test rewrite redirections (if enabled)
    if rewrite_enabled:
        response = api_client.get(expected_unit_picture_url)
        assert response.status_code == 302
        assert response.headers["location"] == PICTURE_URL

        response = api_client.get(expected_unit_entrance_picture_url)
        assert response.status_code == 302
        assert response.headers["location"] == PICTURE_URL


@pytest.mark.parametrize(
    "rewrite_enabled, model, view_name, expected_picture_url",
    [
        [False, Announcement, "announcement", PICTURE_URL],
        [
            True,
            Announcement,
            "announcement",
            "http://testserver/v2/announcement/1/picture/",
        ],
        [False, ErrorMessage, "errormessage", PICTURE_URL],
        [
            True,
            ErrorMessage,
            "errormessage",
            "http://testserver/v2/error_message/1/picture/",
        ],
    ],
)
@pytest.mark.django_db
def test_notification_picture_url_rewrite(
    api_client,
    settings,
    rewrite_enabled,
    model,
    view_name,
    expected_picture_url,
):
    announcement = model.objects.create(
        id=1,
        picture_url=PICTURE_URL,
        active=True,
    )

    settings.PICTURE_URL_REWRITE_ENABLED = rewrite_enabled

    response = get(api_client, reverse(f"{view_name}-list"))
    assert response.data["results"][0]["picture_url"] == expected_picture_url

    response = get(
        api_client, reverse(f"{view_name}-detail", kwargs={"pk": announcement.id})
    )
    assert response.data["picture_url"] == expected_picture_url

    if rewrite_enabled:
        response = api_client.get(expected_picture_url)
        assert response.status_code == 302
        assert response.headers["location"] == PICTURE_URL


@pytest.mark.django_db
def test_unit_picture_404(api_client, unit):
    unit.picture_url = None
    unit.save()
    response = api_client.get(reverse("unit-picture", kwargs={"pk": unit.id}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_unit_entrance_picture_404(api_client, unit_entrance):
    unit_entrance.picture_url = None
    unit_entrance.save()
    response = api_client.get(
        reverse("unitentrance-picture", kwargs={"pk": unit_entrance.id})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_announcement_picture_404(api_client):
    announcement = Announcement.objects.create(
        id=1,
        active=True,
    )
    response = api_client.get(
        reverse("announcement-picture", kwargs={"pk": announcement.id})
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_error_message_picture_404(api_client):
    error_message = ErrorMessage.objects.create(
        id=1,
        active=True,
    )
    response = api_client.get(
        reverse("errormessage-picture", kwargs={"pk": error_message.id})
    )
    assert response.status_code == 404
