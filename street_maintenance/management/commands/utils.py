import logging
import re
import zoneinfo
from datetime import datetime, timedelta

import numpy as np
import requests
from django import db
from django.conf import settings
from django.contrib.gis.geos import LineString, Point
from munigeo.models import AdministrativeDivision, AdministrativeDivisionGeometry

from street_maintenance.models import (
    DEFAULT_SRID,
    GeometryHistory,
    MaintenanceUnit,
    MaintenanceWork,
)

from .constants import (
    AUTORI,
    CONTRACTS,
    EVENT_MAPPINGS,
    EVENTS,
    KUNTEC,
    PROVIDERS,
    ROUTES,
    TIMESTAMP_FORMATS,
    TOKEN,
    UNITS,
    URLS,
    VEHICLES,
    WORKS,
)

logger = logging.getLogger("street_maintenance")
# In seconds
MAX_WORK_LENGTH = 60
VALID_LINESTRING_MAX_POINT_DISTANCE = 0.01


def check_linestring_validity(
    linestring, threshold=VALID_LINESTRING_MAX_POINT_DISTANCE
):
    """
    The LineString is considered invalid if distance between two points is
    greater than VALID_LINESTRING_MAX_POINT_DISTANCE.
    The lower the threshold value the more serve the validating will be.
    """
    prev_coord = None
    for coord in linestring.coords:
        if prev_coord:
            p1 = Point(coord, srid=DEFAULT_SRID)
            p2 = Point(prev_coord, srid=DEFAULT_SRID)
            if p1.distance(p2) > threshold:
                return False
        prev_coord = coord
    return True


def add_geometry_history_objects(objects, points, elem, provider):
    """
    A GeometryHistory instance is added to objects that is passed by reference.
    Returns number of discarded linestring.
    """
    geometry = LineString(points, srid=DEFAULT_SRID)
    if check_linestring_validity(geometry, 0.005):
        objects.append(
            GeometryHistory(
                provider=provider,
                coordinates=geometry.coords,
                timestamp=elem.timestamp,
                events=elem.events,
                geometry=geometry,
            )
        )
        return 0
    else:
        return 1


def get_valid_linestrings(linestring, threshold=VALID_LINESTRING_MAX_POINT_DISTANCE):
    prev_coord = None
    coords = []
    geometries = []
    for coord in linestring.coords:
        if prev_coord:
            p1 = Point(coord, srid=DEFAULT_SRID)
            p2 = Point(prev_coord, srid=DEFAULT_SRID)
            if p1.distance(p2) > threshold:
                if len(coords) > 1:
                    geometries.append(LineString(coords, srid=DEFAULT_SRID))
                    coords = [prev_coord]
                else:
                    coords = []

        coords.append(coord)
        prev_coord = coord

    if len(coords) > 1:
        geometry = LineString(coords, srid=DEFAULT_SRID)
        if check_linestring_validity(geometry, threshold):
            geometries.append(geometry)
    return geometries


def get_linestrings_from_points(objects, queryset, provider):
    """
    Point data is generated into LineStrings. This is done by iterating the
    point data for every MaintenanceUnit for the given provider.
    """
    unit_ids = (
        queryset.order_by("maintenance_unit_id")
        .values_list("maintenance_unit_id", flat=True)
        .distinct("maintenance_unit_id")
    )
    discarded_linestrings = 0
    discarded_points = 0
    for unit_id in unit_ids:
        # Temporary store points to list for LineString creation
        points = []
        qs = queryset.filter(maintenance_unit_id=unit_id).order_by(
            "events", "timestamp"
        )
        prev_timestamp = None
        current_events = None
        prev_geometry = None

        for elem in qs:
            if not current_events:
                current_events = elem.events
            if prev_timestamp and prev_geometry:
                delta_time = abs(elem.timestamp - prev_timestamp)
                # If delta_time is bigger than the MAX_WORK_LENGTH, then we can assume
                # that the work should not be in the same linestring/point or the events
                # has changed.
                if (
                    delta_time.seconds > MAX_WORK_LENGTH
                    or current_events != elem.events
                ):
                    if len(points) > 1:
                        discarded_linestrings += add_geometry_history_objects(
                            objects, points, elem, provider
                        )
                    else:
                        discarded_points += 1
                    current_events = elem.events
                    points = []
            prev_geometry = elem.geometry
            points.append(elem.geometry)
            prev_timestamp = elem.timestamp

        if len(points) > 1:
            discarded_linestrings += add_geometry_history_objects(
                objects, points, elem, provider
            )
    return discarded_linestrings, discarded_points


@db.transaction.atomic
def precalculate_geometry_history(provider):
    """
    Function that populates the GeometryHistory model for a provider.
    LineString geometrys in MaintenanceWorks will be added as they are.
    """
    GeometryHistory.objects.filter(provider=provider).delete()
    objects = []
    queryset = MaintenanceWork.objects.filter(
        maintenance_unit__provider=provider
    ).order_by("timestamp")
    elements_to_remove = []
    # Add works that are linestrings,
    discarded_linestrings = 0
    discarded_points = 0
    for elem in queryset:
        if isinstance(elem.geometry, LineString):
            if check_linestring_validity(elem.geometry):
                objects.append(
                    GeometryHistory(
                        provider=provider,
                        coordinates=elem.geometry.coords,
                        timestamp=elem.timestamp,
                        events=elem.events,
                        geometry=elem.geometry,
                    )
                )
            else:
                discarded_linestrings += 1
            elements_to_remove.append(elem.id)

    # Remove the linestring elements, as they are not needed when generating
    # linestrings from point data
    queryset = queryset.exclude(id__in=elements_to_remove)
    results = get_linestrings_from_points(objects, queryset, provider)
    discarded_linestrings += results[0]
    discarded_points += results[1]
    GeometryHistory.objects.bulk_create(objects)
    logger.info(f"Discarded {discarded_points} Points")
    logger.info(f"Discarded {discarded_linestrings} LineStrings")
    logger.info(f"Created {len(objects)} HistoryGeometry rows for provider: {provider}")


def get_turku_boundary():
    division_turku = AdministrativeDivision.objects.get(name="Turku")
    turku_boundary = AdministrativeDivisionGeometry.objects.get(
        division=division_turku
    ).boundary
    turku_boundary.transform(DEFAULT_SRID)
    return turku_boundary


def get_linestring_in_boundary(linestring, boundary):
    """
    Returns a linestring from the input linestring where all the coordinates
    are inside the boundary. If linestring creation is not possible return False.
    """
    coords = [
        coord
        for coord in linestring.coords
        if boundary.covers(Point(coord, srid=DEFAULT_SRID))
    ]
    if len(coords) > 1:
        linestring = LineString(coords, srid=DEFAULT_SRID)
        return linestring
    else:
        return False


def create_maintenance_works(provider, history_size, fetch_size):
    turku_boundary = get_turku_boundary()
    works = []
    import_from_date_time = datetime.now() - timedelta(days=history_size)
    import_from_date_time = import_from_date_time.replace(
        tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki")
    )
    for unit in MaintenanceUnit.objects.filter(provider=provider):
        response = requests.get(
            URLS[provider][WORKS].format(id=unit.unit_id, history_size=fetch_size)
        )
        if "location_history" in response.json():
            json_data = response.json()["location_history"]
        else:
            logger.warning(f"Location history not found for unit: {unit.unit_id}")
            continue
        for work in json_data:

            timestamp = datetime.strptime(
                work["timestamp"], TIMESTAMP_FORMATS[provider]
            ).replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki"))
            # Discard events older then import_from_date_time as they will
            # never be displayed
            if timestamp < import_from_date_time:
                continue
            coords = work["coords"]
            coords = [float(c) for c in re.sub(r"[()]", "", coords).split(" ")]
            point = Point(coords[0], coords[1], srid=DEFAULT_SRID)
            # discard events outside Turku.
            if not turku_boundary.covers(point):
                continue

            events = []
            for event in work["events"]:
                event_name = event.lower()
                if event_name in EVENT_MAPPINGS:
                    for e in EVENT_MAPPINGS[event_name]:
                        # If mapping value is None, the event is not used.
                        if e:
                            events.append(e)
                else:
                    logger.warning(f"Found unmapped event: {event}")
            # If no events found discard the work
            if len(events) == 0:
                continue
            works.append(
                MaintenanceWork(
                    timestamp=timestamp,
                    maintenance_unit=unit,
                    geometry=point,
                    events=events,
                )
            )
    MaintenanceWork.objects.bulk_create(works)
    logger.info(f"Imported {len(works)} {provider} mainetance works.")
    return len(works)


def create_maintenance_units(provider):
    assert provider in PROVIDERS
    response = requests.get(URLS[provider][UNITS])
    assert (
        response.status_code == 200
    ), "Fetching Maintenance Unit {} status code: {}".format(
        URLS[provider][UNITS], response.status_code
    )
    for unit in response.json():
        # The names of the unit is derived from the events.
        names = [n for n in unit["last_location"]["events"]]
        MaintenanceUnit.objects.create(
            unit_id=unit["id"], names=names, provider=provider
        )
    num_units_imported = MaintenanceUnit.objects.filter(provider=provider).count()
    logger.info(f"Imported {num_units_imported} {provider} mainetance Units.")
    return num_units_imported


def get_autori_contract(access_token):
    response = requests.get(
        URLS[AUTORI][CONTRACTS], headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), "Fetcing Autori Contract {} failed, status code: {}".format(
        URLS[AUTORI][CONTRACTS], response.status_code
    )
    return response.json()[0].get("id", None)


def get_autori_event_types(access_token):
    response = requests.get(
        URLS[AUTORI][EVENTS], headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), " Fetching Autori event types {} failed, status code: {}".format(
        URLS[AUTORI][EVENTS], response.status_code
    )
    return response.json()


def create_dict_from_autori_events(list_of_events):
    events = {}
    for event in list_of_events:
        events[event["id"]] = event["operationName"]
    return events


def create_kuntec_maintenance_units():
    units_url = URLS[KUNTEC][UNITS]
    response = requests.get(units_url)
    assert (
        response.status_code == 200
    ), "Fetching Maintenance Unit {} status code: {}".format(
        units_url, response.status_code
    )
    no_io_din = 0
    for unit in response.json()["data"]["units"]:
        names = []
        if "io_din" in unit:
            on_states = 0
            # example io_din field: {'no': 3, 'label': 'Muu työ', 'state': 0}
            for io in unit["io_din"]:
                if io["state"] == 1:
                    on_states += 1
                    names.append(io["label"])
        # If names, we have a unit with at least one io_din with State On.
        if len(names) > 0:
            unit_id = unit["unit_id"]
            MaintenanceUnit.objects.create(
                unit_id=unit_id, names=names, provider=KUNTEC
            )
        else:
            no_io_din += 1
    logger.info(
        f"Discarding {no_io_din} Kuntec units that do not have a io_din with Status 'On'(1)."
    )
    logger.info(
        f"Imported {MaintenanceUnit.objects.filter(provider=KUNTEC).count()}"
        + " Kuntec mainetance Units."
    )


def create_autori_maintenance_units(access_token):
    response = requests.get(
        URLS[AUTORI][VEHICLES], headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), " Fetching Autori vehicles {} failed, status code: {}".format(
        URLS[AUTORI][VEHICLES], response.status_code
    )
    for unit in response.json():
        names = [unit["vehicleTypeName"]]
        MaintenanceUnit.objects.create(unit_id=unit["id"], names=names, provider=AUTORI)
    logger.info(
        f"Imported {MaintenanceUnit.objects.filter(provider=AUTORI).count()}"
        + " Autori(YIT) mainetance Units."
    )


def get_autori_routes(access_token, contract, history_size):
    now = datetime.now()
    end = now.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki")).strftime(
        TIMESTAMP_FORMATS[AUTORI]
    )
    start = (
        (now - timedelta(days=history_size))
        .replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki"))
        .strftime(TIMESTAMP_FORMATS[AUTORI])
    )
    params = {
        "contract": contract,
        "start": start,
        "end": end,
    }
    response = requests.get(
        URLS[AUTORI][ROUTES],
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    assert (
        response.status_code == 200
    ), "Fetching Autori routes {}, failed, status code: {}".format(
        URLS[AUTORI][ROUTES], response.status_code
    )
    return response.json()


def get_autori_access_token():
    assert settings.AUTORI_SCOPE, "AUTOR_SCOPE not defined in environment."
    assert settings.AUTORI_CLIENT_ID, "AUTOR_CLIENT_ID not defined in environment."
    assert (
        settings.AUTORI_CLIENT_SECRET
    ), "AUTOR_CLIENT_SECRET not defined in environment."
    data = {
        "grant_type": "client_credentials",
        "scope": settings.AUTORI_SCOPE,
        "client_id": settings.AUTORI_CLIENT_ID,
        "client_secret": settings.AUTORI_CLIENT_SECRET,
    }
    response = requests.post(URLS[AUTORI][TOKEN], data=data)
    assert (
        response.status_code == 200
    ), "Fetchin oauth2 token from Autori {} failed, status code: {}".format(
        URLS[AUTORI][TOKEN], response.status_code
    )
    access_token = response.json().get("access_token", None)
    return access_token


def is_nested_coordinates(coordinates):
    return bool(np.array(coordinates).ndim > 1)
