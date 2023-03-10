from datetime import datetime

from street_maintenance.management.commands.constants import (
    DATE_FORMATS,
    INFRAROAD,
    YIT,
)


def get_yit_vehicles_mock_data(num_elements):
    data = [
        {"id": "82260ff7-589e-4cee-a8e0-124b615381f1", "vehicleTypeName": "Huoltoauto"},
        {
            "id": "77396829-6275-4dbe-976f-f9d4f5254653",
            "vehicleTypeName": "Kuorma-auto",
        },
    ]
    assert num_elements <= len(data)
    return data[:num_elements]


def get_yit_event_types_mock_data():
    data = [
        {
            "id": "a4f6188f-8c25-4f42-89be-f5a1bd7d833a",
            "operationName": "Auraus ja sohjonpoisto",
        },
        {"id": "a51e8e4c-8b16-4132-a882-70f6624c1f2b", "operationName": "Suolaus"},
    ]
    return data


def get_yit_contract_mock_data():
    return "d73447e6-df70-4f4a-817d-3387b58aca6c"


def get_yit_routes_mock_data(num_elements):
    current_date = datetime.now().date().strftime(DATE_FORMATS[YIT])
    data = [
        {
            "vehicleType": "82260ff7-589e-4cee-a8e0-124b615381f1",
            "length": 0.0,
            "geography": {
                "crs": None,
                "features": [
                    {
                        "geometry": {
                            "coordinates": [
                                [22.315554108363656, 60.47901418729062],
                                [22.31555399713308, 60.47901429688299],
                            ],
                            "type": "LineString",
                        },
                        "properties": {
                            "streetAddress": "Polttolaitoksenkatu 13, Turku",
                            "featureType": "StreetAddress",
                        },
                        "type": "Feature",
                    }
                ],
                "type": "FeatureCollection",
            },
            "created": f"{current_date}T11:52:00.5136066Z",
            "updated": f"{current_date}T11:52:00.5136066Z",
            "deleted": False,
            "id": "9c566b34-2bb5-46b0-9c0a-99f53eada2d2",
            "user": "442a5ab2-d58c-4c22-bae2-bcf55327cde7",
            "contract": "d73447e6-df70-4f4a-817d-3387b58aca6c",
            "startTime": f"{current_date}T11:50:21.708Z",
            "endTime": f"{current_date}T11:50:21.709Z",
            "operations": ["a51e8e4c-8b16-4132-a882-70f6624c1f2b"],
        },
        {
            # Note, the MaintenanceUnit is retrieved by the vehicleType
            "vehicleType": "82260ff7-589e-4cee-a8e0-124b615381f1",
            "length": 21.0,
            "geography": {
                "crs": None,
                "features": [
                    {
                        "geometry": {
                            "coordinates": [
                                [22.308685, 60.471465],
                                [22.308758333333337, 60.47151166666666],
                                [22.308844999999998, 60.47154999999999],
                                [22.30887476486449, 60.471557320473416],
                            ],
                            "type": "LineString",
                        },
                        "properties": {
                            "streetAddress": "Koroistenkaari, Turku",
                            "featureType": "StreetAddress",
                        },
                        "type": "Feature",
                    }
                ],
                "type": "FeatureCollection",
            },
            "created": f"{current_date}T11:50:58.6173037Z",
            "updated": f"{current_date}T11:50:58.6173037Z",
            "deleted": False,
            "id": "aaee2c3b-4296-44b3-aba0-82b859d4eea8",
            "user": "442a5ab2-d58c-4c22-bae2-bcf55327cde7",
            "contract": "d73447e6-df70-4f4a-817d-3387b58aca6c",
            "startTime": f"{current_date}T11:48:44.694Z",
            "endTime": f"{current_date}T11:48:46.984Z",
            "operations": ["a51e8e4c-8b16-4132-a882-70f6624c1f2b"],
        },
    ]
    assert num_elements <= len(data)
    return data[:num_elements]


# Both Destia and Infraroad uses the fluentprogress API
def get_fluentprogress_works_mock_data(num_elements):
    current_date = datetime.now().date().strftime(DATE_FORMATS[INFRAROAD])
    location_history = [
        {
            "timestamp": f"{current_date} 08:29:49",
            "coords": "(22.24957474 60.49515401)",
            "events": ["au"],
        },
        {
            "timestamp": f"{current_date} 08:29:28",
            "coords": "(22.24946401 60.49515848)",
            "events": ["au", "sivuaura", "sirotin"],
        },
        {
            "timestamp": f"{current_date} 08:28:32",
            "coords": "(22.24944127 60.49519463)",
            "events": ["hiekoitus"],
        },
    ]
    assert num_elements <= len(location_history)
    data = {"location_history": location_history[:num_elements]}
    return data


def get_fluentprogress_units_mock_data(num_elements):
    current_date = datetime.now().date().strftime(DATE_FORMATS[INFRAROAD])
    data = [
        {
            "id": 2817625,
            "last_location": {
                "timestamp": f"{current_date} 06:31:34",
                "coords": "(22.249642023816705 60.49569119699299)",
                "events": ["au"],
            },
        },
        {
            "id": 12891825,
            "last_location": {
                "timestamp": f"{current_date} 08:29:49",
                "coords": "(22.24957474 60.49515401)",
                "events": ["Kenttien hoito"],
            },
        },
    ]
    assert num_elements <= len(data)
    return data[:num_elements]


def get_kuntec_works_mock_data(num_elements):
    current_date = datetime.now().date().strftime(DATE_FORMATS[INFRAROAD])
    routes = [
        {
            "route_id": 3980827390,
            "type": "route",
            "start": {
                "time": f"{current_date}T14:54:31Z",
                "address": "M\u00e4likk\u00e4l\u00e4, 21280 Turku, Suomi",
                "lat": 60.47185,
                "lng": 22.21618,
            },
            "avg_speed": 18,
            "max_speed": 43,
            "end": {
                "time": f"{current_date}T15:05:56Z",
                "address": "Ihalantie 7, 21200 Raisio, Suomi",
                "lat": 60.47945,
                "lng": 22.18221,
            },
            "distance": 3565,
            "polyline": "a|apJcbrfC@HEpQYdEi@rDeAnE{Sji@eOjp@qEpb@uUlkA?T@TFRHLNDb@@b@Cd@Sb@i@XeArCeJv@{@z@c@h@E~@JdC"
            + "n@FCBE@C@G@G@K?KEsA@cBAI?K?}BBWF[DOBMJQBCB?D?JHFHDN@FBNBLBD@BDBES?EAEAEI[CM@EXt@Uw@Tz@BHA?EQEMO_@@HIII"
            + "IAE?QAc@EXCECBEDAHWdBENAF?D?D?v@DhE@JCQ?M@M?_@@oFBKF]",
        },
        {
            "route_id": 3984019243,
            "type": "route",
            "start": {
                "time": f"{current_date}T11:16:00Z",
                "address": "Tuontikatu 180, 20200 Turku, Suomi",
                "lat": 60.44447,
                "lng": 22.21462,
            },
            "avg_speed": 18,
            "max_speed": 43,
            "end": {
                "time": f"{current_date}T11:21:55Z",
                "address": "Tuontikatu, 20200 Turku, Suomi",
                "lat": 60.44754,
                "lng": 22.21391,
            },
            "distance": 1799,
            "polyline": "}p|oJkxqfCt@|AtAtELT@JFd@d@nBX`AfAlFLl@Rv@xHv[T^p@~@DJ@B?DDPD@KUACCIQUg@i@]q@m@_C{Loi@AUIKCEU"
            + "_@Oc@{@yCw@aB_BaB_A_@_CI{F[IFGLI^A`@?d@IfCGxA",
        },
    ]

    assert num_elements <= len(routes)
    data = {"data": {"units": [{"routes": routes[:num_elements]}]}}
    return data


def get_kuntec_units_mock_data(num_elements):
    null = None
    units = [
        {
            "unit_id": 150635,
            "box_id": 27953713,
            "company_id": 5495,
            "country_code": "FI",
            "label": "1100781186",
            "number": "HAKA 2",
            "shortcut": "",
            "vehicle_title": null,
            "car_reg_certificate": "",
            "vin": null,
            "type": "car",
            "icon": "tractor",
            "lat": 60.46423,
            "lng": 22.43703,
            "direction": 161,
            "speed": null,
            "mileage": 11779869,
            "last_update": "2023-02-25T13:20:56Z",
            "ignition_total_time": 7683589,
            "state": {
                "name": "nodata",
                "start": "2023-02-25T12:40:53Z",
                "duration": 148756,
                "debug_info": {
                    "boxId": 27953713,
                    "carId": 150635,
                    "msg": "POWEROFF",
                    "lastUpdate": 1677331256,
                    "lastValues": null,
                },
            },
            "movement_state": {
                "name": "nodata",
                "start": "2023-02-25T12:40:53Z",
                "duration": 151159,
            },
            "fuel_type": "",
            "avg_fuel_consumption": {"norm": 0, "measurement": "l/100km"},
            "created_at": "2019-11-05T10:10:38Z",
            "io_din": [
                {"no": 1, "label": "Auraus", "state": 1},
                {"no": 2, "label": "Hiekoitus", "state": 1},
                {"no": 3, "label": "Muu ty\u00f6", "state": 0},
            ],
        },
        {
            "unit_id": 150662,
            "box_id": 27953746,
            "company_id": 5495,
            "country_code": "FI",
            "label": "1101049692",
            "number": "TAKKU 1",
            "shortcut": "",
            "vehicle_title": null,
            "car_reg_certificate": "",
            "vin": null,
            "type": "car",
            "icon": "tractor",
            "lat": 60.55185,
            "lng": 22.20567,
            "direction": 213,
            "speed": null,
            "mileage": 10537795,
            "last_update": "2023-02-26T10:02:03Z",
            "ignition_total_time": 0,
            "state": {
                "name": "nodata",
                "start": "2023-02-26T09:33:37Z",
                "duration": 74289,
                "debug_info": {
                    "boxId": 27953746,
                    "carId": 150662,
                    "msg": "OTHER",
                    "lastUpdate": 1677405723,
                    "lastValues": {"VOLTAGE": "14289"},
                },
            },
            "movement_state": {
                "name": "nodata",
                "start": "2023-02-26T09:33:37Z",
                "duration": 75995,
            },
            "fuel_type": "",
            "avg_fuel_consumption": {"norm": 0, "measurement": "l/100km"},
            "created_at": "2019-11-05T10:39:46Z",
            "io_din": [
                {"no": 1, "label": "Auraus", "state": 1},
                {"no": 2, "label": "Hiekoitus", "state": 0},
                {"no": 3, "label": "Muu ty\u00f6", "state": 0},
            ],
        },
        {
            "unit_id": 150662,
            "box_id": 27953746,
            "company_id": 5495,
            "country_code": "FI",
            "label": "1101049692",
            "number": "TAKKU 1",
            "shortcut": "",
            "vehicle_title": null,
            "car_reg_certificate": "",
            "vin": null,
            "type": "car",
            "icon": "tractor",
            "lat": 60.55185,
            "lng": 22.20567,
            "direction": 213,
            "speed": null,
            "mileage": 10537795,
            "last_update": "2023-02-26T10:02:03Z",
            "ignition_total_time": 0,
            "state": {
                "name": "nodata",
                "start": "2023-02-26T09:33:37Z",
                "duration": 74289,
                "debug_info": {
                    "boxId": 27953746,
                    "carId": 150662,
                    "msg": "OTHER",
                    "lastUpdate": 1677405723,
                    "lastValues": {"VOLTAGE": "14289"},
                },
            },
            "movement_state": {
                "name": "nodata",
                "start": "2023-02-26T09:33:37Z",
                "duration": 75995,
            },
            "fuel_type": "",
            "avg_fuel_consumption": {"norm": 0, "measurement": "l/100km"},
            "created_at": "2019-11-05T10:39:46Z",
            "io_din": [
                {"no": 1, "label": "Auraus", "state": 1},
                {"no": 2, "label": "Hiekoitus", "state": 0},
                {"no": 3, "label": "Muu ty\u00f6", "state": 0},
            ],
        },
    ]
    assert num_elements <= len(units)
    data = {"data": {"units": units[:num_elements]}}
    return data
