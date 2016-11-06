import pytest
from fixtures import *
from data import observation_raw_data
from rest_framework.reverse import reverse

@pytest.mark.django_db
def test__create_observation(api_client, service, unit):
    url = reverse(
        'unit-detail',
        kwargs={'pk': unit.pk}) + '?include=observable_properties'
    response = api_client.get(url)

    observable_properties = response.data['observable_properties']
    for prop in observable_properties:
        otype = prop.observation_type
        raw_data = observation_raw_data(otype, unit)
        url = reverse('observation-detail')
        print(raw_data)
        api_client.post(url, raw_data)
