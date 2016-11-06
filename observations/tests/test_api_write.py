import pytest
from fixtures import *
from data import observation_raw_data
from rest_framework.reverse import reverse

@pytest.mark.django_db
def test__create_observation(api_client, observable_property, unit):
    url = reverse(
        'unit-detail',
        kwargs={'pk': unit.pk}) + '?include=observable_properties'
    response = api_client.get(url)
    print(response.data)
    observable_properties = response.data['observable_properties']
    assert len(observable_properties) > 0
    for prop in observable_properties:
        otype = prop['observation_type']
        raw_data = observation_raw_data(otype, unit)
        url = reverse('observation-list')
        api_client.post(url, raw_data)
