import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from services.models import Announcement, ErrorMessage
from services.tests.utils import get


def create_notifications(model):
    model.objects.create(
        title_en="Visible notification",
        title_fi="Esimerkki-ilmoitus",
        content_en="About the alert...",
        active=True,
    )
    model.objects.create(
        title="Hidden notification", content="About the alert...", active=False
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@pytest.mark.parametrize("endpoint", ["announcement-list", "errormessage-list"])
def test_not_allowed_methods(api_client, method, endpoint):
    assert (
        getattr(api_client, method)(reverse(endpoint), format="json").status_code == 405
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "notification_model, endpoint",
    [
        (Announcement, "announcement-list"),
        (ErrorMessage, "errormessage-list"),
    ],
)
def test_get_notification_list(api_client, notification_model, endpoint):
    create_notifications(model=notification_model)
    response = get(api_client, reverse(endpoint))
    results = response.data["results"]

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert results[0].get("title") == {
        "fi": "Esimerkki-ilmoitus",
        "en": "Visible notification",
    }
    assert results[0].get("content") == {
        "en": "About the alert...",
    }
