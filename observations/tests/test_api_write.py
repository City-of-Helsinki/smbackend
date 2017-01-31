import pytest
from fixtures import *
from observations.models import Observation
from data import observation_raw_data
from rest_framework.reverse import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.urlresolvers import reverse as django_reverse


def authenticate_user(api_client, user):
    url = django_reverse('api-auth-token')
    response = api_client.post(url, user)
    token = response.data['token']
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + token)

@pytest.mark.django_db
def test__create_observation(api_client, observable_property, unit, user):
    url = reverse(
        'unit-detail',
        kwargs={'pk': unit.pk}) + '?include=observable_properties'
    response = api_client.get(url)
    observable_properties = response.data['observable_properties']
    assert len(observable_properties) > 0
    assert Observation.objects.count() == 0

    authenticate_user(api_client, user)

    count = 0
    for prop in observable_properties:
        otype = prop['id']
        for raw_data in observation_raw_data(otype, unit, allowed_values=[
                v['identifier'] for v in prop['allowed_values']
        ]):
            print(raw_data)
            url = reverse('observation-list')
            current_time = timezone.now()
            response = api_client.post(url, raw_data)

            assert response.status_code == 201
            count += 1
            data = response.data
            observation_time = datetime.strptime(
                data['time'],
                "%Y-%m-%dT%H:%M:%S.%f%z")
            assert observation_time - current_time < timedelta(seconds=1)
            assert data['value'] == raw_data['value']
            assert data['property'] == raw_data['property']
            assert data['unit'] == raw_data['unit']
    assert Observation.objects.count() == count
