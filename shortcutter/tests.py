import pytest
from django.test import Client
from django.urls import reverse
from django.test.utils import override_settings


@pytest.fixture
def client():
    return Client()


@override_settings(SHORTCUTTER_UNIT_URL='https://example.com/unit/{id}')
@pytest.mark.django_db
def test_unit_short_url(client):
    url = reverse('shortcutter-unit-url', kwargs=dict(unit_id=1234))
    resp = client.get(url)
    assert resp.status_code == 302
    assert resp.url == 'https://example.com/unit/1234'


@override_settings(SHORTCUTTER_UNIT_URL=None)
@pytest.mark.django_db
def test_unit_short_url_no_config(client):
    url = reverse('shortcutter-unit-url', kwargs=dict(unit_id=1234))
    resp = client.get(url)
    assert resp.status_code == 501
