import requests
from django.conf import settings
from munigeo.models import AdministrativeDivision, AdministrativeDivisionGeometry

from street_maintenance.models import DEFAULT_SRID
from .constants import AUTORI_CONTRACTS_URL, AUTORI_EVENTS_URL,AUTORI_ROUTES_URL,AUTORI_TOKEN_URL


def get_turku_boundry():
    division_turku = AdministrativeDivision.objects.get(name="Turku")
    turku_boundary = AdministrativeDivisionGeometry.objects.get(
        division=division_turku
    ).boundary
    turku_boundary.transform(DEFAULT_SRID)
    return turku_boundary


def get_autori_contract(access_token):
    response = requests.get(
        AUTORI_CONTRACTS_URL, headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    return response.json()[0].get("id", None)


def get_autori_event_types(access_token):
    response = requests.get(
        AUTORI_EVENTS_URL, headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    return response.json()


def create_dict_from_autori_events(list_of_events):
    events = {}
    for event in list_of_events:
        events[event["id"]] = event["operationName"]
    return event


def get_autori_routes(access_token, contract):
    # Todo get times and calculate start -3 days etc
    params = {
        "contract": contract,
        "start": "2022-10-1 00:00:00Z",
        "end": "2022-10-6 00:00:00Z",
    }
    response = requests.get(
        AUTORI_ROUTES_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    assert response.status_code == 200
    return response.json()


def get_autori_access_token():

    test_data = {
        "grant_type": "client_credentials",
        "scope": settings.AUTORI_SCOPE,
        "client_id": settings.AUTORI_CLIENT_ID,
        "client_secret": settings.AUTORI_CLIENT_SECRET,
    }
    response = requests.post(AUTORI_TOKEN_URL, data=test_data)
    assert response.status_code == 200
    access_token = response.json().get("access_token", None)
    return access_token
