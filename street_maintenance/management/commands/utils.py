import logging
import re
import zoneinfo
from datetime import datetime, timedelta

import numpy as np
import polyline
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
    CONTRACTS,
    EVENT_MAPPINGS,
    EVENTS,
    KUNTEC,
    KUNTEC_KEY,
    ROUTES,
    TIMESTAMP_FORMATS,
    TOKEN,
    UNITS,
    URLS,
    VEHICLES,
    WORKS,
    YIT,
)

logger = logging.getLogger("street_maintenance")
# In seconds
MAX_WORK_LENGTH = 60
VALID_LINESTRING_MAX_POINT_DISTANCE = 0.01


def get_turku_boundary():
    division_turku = AdministrativeDivision.objects.get(name="Turku")
    turku_boundary = AdministrativeDivisionGeometry.objects.get(
        division=division_turku
    ).boundary
    turku_boundary.transform(DEFAULT_SRID)
    return turku_boundary


TURKU_BOUNDARY = get_turku_boundary()


def get_json_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        logger.warning(
            f"Fetching Maintenance Unit {url} status code: {response.status_code} response: {response.content}"
        )
        return {}
    return response.json()


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
    logger.info(f"Discarded {discarded_points} points in linestring generation")
    logger.info(f"Discarded {discarded_linestrings} invalid LineStrings")
    logger.info(f"Created {len(objects)} HistoryGeometry rows for provider: {provider}")


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


def handle_unit(filter, objs_to_delete):
    num_created = 0
    queryset = MaintenanceUnit.objects.filter(**filter)
    queryset_count = queryset.count()
    if queryset_count == 0:
        MaintenanceUnit.objects.create(**filter)
        num_created += 1
    else:
        # Keep the first element and if duplicates leave them for deletion.
        id = queryset.first().id
        if id in objs_to_delete:
            objs_to_delete.remove(id)
    return num_created


def handle_work(filter, objs_to_delete):
    num_created = 0
    queryset = MaintenanceWork.objects.filter(**filter)
    queryset_count = queryset.count()

    if queryset_count == 0:
        MaintenanceWork.objects.create(**filter)
        num_created += 1
    else:
        # Keep the first element and if duplicates leave them for deletion.
        id = queryset.first().id
        if id in objs_to_delete:
            objs_to_delete.remove(queryset.first().id)
    return num_created


@db.transaction.atomic
def create_yit_maintenance_works(access_token, history_size):
    contract = get_yit_contract(access_token)
    list_of_events = get_yit_event_types(access_token)
    event_name_mappings = create_dict_from_yit_events(list_of_events)
    routes = get_yit_routes(access_token, contract, history_size)
    objs_to_delete = list(
        MaintenanceWork.objects.filter(maintenance_unit__provider=YIT).values_list(
            "id", flat=True
        )
    )
    num_created = 0
    for route in routes:
        if len(route["geography"]["features"]) > 1:
            logger.warning(
                f"Route contains multiple features. {route['geography']['features']}"
            )
        coordinates = route["geography"]["features"][0]["geometry"]["coordinates"]

        if is_nested_coordinates(coordinates) and len(coordinates) > 1:
            geometry = LineString(coordinates, srid=DEFAULT_SRID)
        else:
            # Remove other data, contains faulty linestrings.
            continue
        # Create linestring that is inside the boundary of Turku
        # and discard parts of the geometry if they are outside the boundary.
        geometry = get_linestring_in_boundary(geometry, TURKU_BOUNDARY)
        if not geometry:
            continue
        events = []
        original_event_names = []
        operations = route["operations"]
        for operation in operations:
            event_name = event_name_mappings[operation].lower()
            if event_name in EVENT_MAPPINGS:
                for e in EVENT_MAPPINGS[event_name]:
                    # If mapping value is None, the event is not used.
                    if e:
                        if e not in events:
                            events.append(e)
                        original_event_names.append(event_name_mappings[operation])
            else:
                logger.warning(
                    f"Found unmapped event: {event_name_mappings[operation]}"
                )

        # If no events found discard the work
        if len(events) == 0:
            continue
        if len(route["geography"]["features"]) > 1:
            logger.warning(
                f"Route contains multiple features. {route['geography']['features']}"
            )
        unit_id = route["vehicleType"]
        try:
            unit = MaintenanceUnit.objects.get(unit_id=unit_id)
        except MaintenanceUnit.DoesNotExist:
            logger.warning(f"Maintenance unit: {unit_id}, not found.")
            continue
        filter = {
            "timestamp": route["startTime"],
            "maintenance_unit": unit,
            "geometry": geometry,
            "events": events,
            "original_event_names": original_event_names,
        }
        num_created += handle_work(filter, objs_to_delete)

    MaintenanceWork.objects.filter(id__in=objs_to_delete).delete()
    return num_created, len(objs_to_delete)


@db.transaction.atomic
def create_kuntec_maintenance_works(history_size):
    num_created = 0
    now = datetime.now()
    start = (now - timedelta(days=history_size)).strftime(TIMESTAMP_FORMATS[KUNTEC])
    end = now.strftime(TIMESTAMP_FORMATS[KUNTEC])
    objs_to_delete = list(
        MaintenanceWork.objects.filter(maintenance_unit__provider=KUNTEC).values_list(
            "id", flat=True
        )
    )
    for unit in MaintenanceUnit.objects.filter(provider=KUNTEC):
        url = URLS[KUNTEC][WORKS].format(
            key=KUNTEC_KEY, start=start, end=end, unit_id=unit.unit_id
        )
        json_data = get_json_data(url)
        if "data" in json_data:
            for unit_data in json_data["data"]["units"]:
                for route in unit_data["routes"]:
                    events = []
                    original_event_names = []
                    # Routes of type 'stop' are discarded.
                    if route["type"] == "route":
                        # Check for mapped events to include as works.
                        for name in unit.names:
                            event_name = name.lower()
                            if event_name in EVENT_MAPPINGS:
                                for e in EVENT_MAPPINGS[event_name]:
                                    # If mapping value is None, the event is not used.
                                    if e:
                                        if e not in events:
                                            events.append(e)
                                        original_event_names.append(name)
                            else:
                                logger.warning(f"Found unmapped event: {event_name}")
                    # If route has mapped event(s) and contains a polyline add work.
                    if len(events) > 0 and "polyline" in route:
                        coords = polyline.decode(route["polyline"], geojson=True)
                        if len(coords) > 1:
                            geometry = LineString(coords, srid=DEFAULT_SRID)
                        else:
                            continue
                        # Create linestring that is inside the boundary of Turku
                        # and discard parts of the geometry if they are outside the boundary.
                        geometry = get_linestring_in_boundary(geometry, TURKU_BOUNDARY)
                        if not geometry:
                            continue
                        timestamp = route["start"]["time"]
                        filter = {
                            "timestamp": timestamp,
                            "maintenance_unit": unit,
                            "geometry": geometry,
                            "events": events,
                            "original_event_names": original_event_names,
                        }
                        num_created += handle_work(filter, objs_to_delete)

    MaintenanceWork.objects.filter(id__in=objs_to_delete).delete()
    return num_created, len(objs_to_delete)


@db.transaction.atomic
def create_maintenance_works(provider, history_size, fetch_size):
    turku_boundary = get_turku_boundary()
    num_created = 0

    import_from_date_time = datetime.now() - timedelta(days=history_size)
    import_from_date_time = import_from_date_time.replace(
        tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki")
    )
    objs_to_delete = list(
        MaintenanceWork.objects.filter(maintenance_unit__provider=provider).values_list(
            "id", flat=True
        )
    )
    for unit in MaintenanceUnit.objects.filter(provider=provider):
        json_data = get_json_data(
            URLS[provider][WORKS].format(id=unit.unit_id, history_size=fetch_size)
        )
        if "location_history" in json_data:
            json_data = json_data["location_history"]
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
            original_event_names = []
            for event in work["events"]:
                event_name = event.lower()
                if event_name in EVENT_MAPPINGS:
                    for e in EVENT_MAPPINGS[event_name]:
                        # If mapping value is None, the event is not used.
                        if e:
                            if e not in events:
                                events.append(e)
                            original_event_names.append(event)
                else:
                    logger.warning(f"Found unmapped event: {event}")
            # If no events found discard the work
            if len(events) == 0:
                continue
            filter = {
                "timestamp": timestamp,
                "maintenance_unit": unit,
                "geometry": point,
                "events": events,
                "original_event_names": original_event_names,
            }
            num_created += handle_work(filter, objs_to_delete)

    MaintenanceWork.objects.filter(id__in=objs_to_delete).delete()
    return num_created, len(objs_to_delete)


@db.transaction.atomic
def create_maintenance_units(provider):
    num_created = 0
    objs_to_delete = list(
        MaintenanceUnit.objects.filter(provider=provider).values_list("id", flat=True)
    )
    for unit in get_json_data(URLS[provider][UNITS]):
        # The names of the unit is derived from the events.
        names = [n for n in unit["last_location"]["events"]]
        filter = {
            "unit_id": unit["id"],
            "names": names,
            "provider": provider,
        }
        num_created += handle_unit(filter, objs_to_delete)

    MaintenanceUnit.objects.filter(id__in=objs_to_delete).delete()
    return num_created, len(objs_to_delete)


def get_yit_contract(access_token):
    response = requests.get(
        URLS[YIT][CONTRACTS], headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), "Fetcing YIT Contract {} failed, status code: {}".format(
        URLS[YIT][CONTRACTS], response.status_code
    )
    return response.json()[0].get("id", None)


def get_yit_event_types(access_token):
    response = requests.get(
        URLS[YIT][EVENTS], headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), " Fetching YIT event types {} failed, status code: {}".format(
        URLS[YIT][EVENTS], response.status_code
    )
    return response.json()


def create_dict_from_yit_events(list_of_events):
    events = {}
    for event in list_of_events:
        events[event["id"]] = event["operationName"]
    return events


@db.transaction.atomic
def create_kuntec_maintenance_units():
    json_data = get_json_data(URLS[KUNTEC][UNITS])
    no_io_din = 0
    num_created = 0
    objs_to_delete = list(
        MaintenanceUnit.objects.filter(provider=KUNTEC).values_list("id", flat=True)
    )
    for unit in json_data["data"]["units"]:
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
            filter = {
                "unit_id": unit["unit_id"],
                "names": names,
                "provider": KUNTEC,
            }
            num_created += handle_unit(filter, objs_to_delete)
        else:
            no_io_din += 1
    MaintenanceUnit.objects.filter(id__in=objs_to_delete).delete()
    logger.info(
        f"Discarding {no_io_din} Kuntec units that do not have a io_din with Status 'On'(1)."
    )
    return num_created, len(objs_to_delete)


def get_yit_vehicles(access_token):
    response = requests.get(
        URLS[YIT][VEHICLES], headers={"Authorization": f"Bearer {access_token}"}
    )
    assert (
        response.status_code == 200
    ), " Fetching YIT vehicles {} failed, status code: {}".format(
        URLS[YIT][VEHICLES], response.status_code
    )
    return response.json()


@db.transaction.atomic
def create_yit_maintenance_units(access_token):
    vehicles = get_yit_vehicles(access_token)
    num_created = 0
    objs_to_delete = list(
        MaintenanceUnit.objects.filter(provider=YIT).values_list("id", flat=True)
    )
    for unit in vehicles:
        names = [unit["vehicleTypeName"]]
        filter = {
            "unit_id": unit["id"],
            "names": names,
            "provider": YIT,
        }
        num_created += handle_unit(filter, objs_to_delete)

    MaintenanceUnit.objects.filter(id__in=objs_to_delete).delete()
    return num_created, len(objs_to_delete)


def get_yit_routes(access_token, contract, history_size):
    now = datetime.now()
    end = now.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki")).strftime(
        TIMESTAMP_FORMATS[YIT]
    )
    start = (
        (now - timedelta(days=history_size))
        .replace(tzinfo=zoneinfo.ZoneInfo("Europe/Helsinki"))
        .strftime(TIMESTAMP_FORMATS[YIT])
    )
    params = {
        "contract": contract,
        "start": start,
        "end": end,
    }
    response = requests.get(
        URLS[YIT][ROUTES],
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    assert (
        response.status_code == 200
    ), "Fetching YIT routes {}, failed, status code: {}".format(
        URLS[YIT][ROUTES], response.status_code
    )
    return response.json()


def get_yit_access_token():
    """
    Note the IP address of the host calling Autori API (hosts YIT data) must be
    given for whitelistning.
    """
    assert settings.YIT_SCOPE, "YIT_SCOPE not defined in environment."
    assert settings.YIT_CLIENT_ID, "YIT_CLIENT_ID not defined in environment."
    assert settings.YIT_CLIENT_SECRET, "YIT_CLIENT_SECRET not defined in environment."
    data = {
        "grant_type": "client_credentials",
        "scope": settings.YIT_SCOPE,
        "client_id": settings.YIT_CLIENT_ID,
        "client_secret": settings.YIT_CLIENT_SECRET,
    }
    response = requests.post(URLS[YIT][TOKEN], data=data)
    assert (
        response.status_code == 200
    ), "Fetchin oauth2 token from YIT {} failed, status code: {}".format(
        URLS[YIT][TOKEN], response.status_code
    )
    access_token = response.json().get("access_token", None)
    return access_token


def is_nested_coordinates(coordinates):
    return bool(np.array(coordinates).ndim > 1)
