import pytest
from rest_framework.test import APIClient
from django.contrib.gis.geos import LineString, linestring
from .utils import generate_coords

from ..models import(
    BicycleNetwork,
    BicycleNetworkPart,
)
@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
@pytest.fixture
def bicycle_network():
    main_netowrk = BicycleNetwork.objects.create(
        name="main_network"
    )
    local_network = BicycleNetwork.objects.create(
        name="local_network"
    )
    return [main_netowrk, local_network]


@pytest.mark.django_db
@pytest.fixture
def bicycle_network_part(bicycle_network):
    main_network = bicycle_network[0]
    local_network = bicycle_network[1]
    line_string = LineString(generate_coords(22.2, 60.2, 22.3, 60.4, 10))
    bnp1 = BicycleNetworkPart.objects.create(
        bicycle_network=main_network, 
        geometry=line_string)
    
    line_string = LineString(generate_coords(22.1, 60.1, 22.0, 59.8, 10))
    bnp2 = BicycleNetworkPart.objects.create(
        bicycle_network=local_network, 
        geometry=line_string)
    
    return [bnp1, bnp2]
    
