import logging
import zoneinfo
from datetime import datetime, timedelta

import requests
from django.conf import settings
from munigeo.models import AdministrativeDivision, AdministrativeDivisionGeometry

from street_maintenance.models import DEFAULT_SRID, MaintenanceUnit

from .constants import (
    AUTORI_CONTRACTS_URL,
    AUTORI_EVENTS_URL,
    AUTORI_ROUTES_URL,
    AUTORI_TOKEN_URL,
    INFRAROAD_UNITS_URL,
)

logger = logging.getLogger("street_maintenance")


def get_turku_boundary():
    division_turku = AdministrativeDivision.objects.get(name="Turku")
    turku_boundary = AdministrativeDivisionGeometry.objects.get(
        division=division_turku
    ).boundary
    turku_boundary.transform(DEFAULT_SRID)
    return turku_boundary


# def get_infrarod_unit_ids():
#     response = requests.get(INFRAROAD_UNITS_URL)
#     assert (
#         response.status_code == 200
#     ), "Fetching Infrarod Maintenance Unit {}, status code: {}".format(
#         INFRAROAD_UNITS_URL, response.status_code
#     )
#     ids = []
#     for unit in response.json():
#         ids.append(unit["id"])
#     return ids
def create_infraroad_maintenance_units():
    response = requests.get(INFRAROAD_UNITS_URL)
    assert (
        response.status_code == 200
    ), "Fetching Maintenance Unit {} status code: {}".format(
        INFRAROAD_UNITS_URL, response.status_code
    )
    for unit in response.json():
        MaintenanceUnit.objects.create(
            unit_id=unit["id"], provider=MaintenanceUnit.INFRAROAD
        )
    logger.info(
        f"Imported {MaintenanceUnit.objects.all().count()} Infraroad mainetance Units."
    )


def get_autori_contract(access_token):
    response = requests.get(
        AUTORI_CONTRACTS_URL, headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), "Fetcing Autori Contract {} failed, status code: {}".format(
        AUTORI_CONTRACTS_URL, response.status_code
    )
    return response.json()[0].get("id", None)


def get_autori_event_types(access_token):
    response = requests.get(
        AUTORI_EVENTS_URL, headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), " Fetching Autori event types {} failed, status code: {}".format(
        AUTORI_EVENTS_URL, response.status_code
    )
    return response.json()


def create_dict_from_autori_events(list_of_events):
    events = {}
    for event in list_of_events:
        events[event["id"]] = event["operationName"]
    return events


def get_autori_routes(access_token, contract):
    now = datetime.now()
    end = now.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki")).strftime(
        "%Y-%m-%d %H:%M:%S%z"
    )
    start = (
        (now - timedelta(days=5))
        .replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki"))
        .strftime("%Y-%m-%d %H:%M:%S%z")
    )
    params = {
        "contract": contract,
        "start": start,
        "end": end,
    }
    response = requests.get(
        AUTORI_ROUTES_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    assert (
        response.status_code == 200
    ), "Fetching Autori routes {}, failed, status code: {}".format(
        AUTORI_ROUTES_URL, response.status_code
    )
    return response.json()


def get_autori_access_token():

    test_data = {
        "grant_type": "client_credentials",
        "scope": settings.AUTORI_SCOPE,
        "client_id": settings.AUTORI_CLIENT_ID,
        "client_secret": settings.AUTORI_CLIENT_SECRET,
    }
    response = requests.post(AUTORI_TOKEN_URL, data=test_data)
    assert (
        response.status_code == 200
    ), "Fetchin oauth2 token from Autori {} failed, status code: {}".format(
        AUTORI_TOKEN_URL, response.status_code
    )
    access_token = response.json().get("access_token", None)
    return access_token
