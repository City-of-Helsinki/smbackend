from io import StringIO

import pytest
from django.core.management import call_command
from freezegun import freeze_time

from exceptional_situations.models import (
    Situation,
    SituationAnnouncement,
    SituationLocation,
    SituationType,
)

data = [
    {
        "type": "Feature",
        "geometry": {
            "type": "MultiLineString",
            "coordinates": [
                [
                    [22.317385, 60.488663],
                    [22.317304, 60.488723],
                    [22.317274, 60.488745],
                    [22.316534, 60.489268],
                    [22.316126, 60.489559],
                    [22.315814, 60.489772],
                    [22.314938, 60.490371],
                    [22.314302, 60.490777],
                    [22.313629, 60.491174],
                    [22.313013, 60.491516],
                    [22.312365, 60.491868],
                    [22.31148, 60.492311],
                    [22.310859, 60.492607],
                    [22.310689, 60.492689],
                    [22.310625, 60.492717],
                    [22.309978, 60.493002],
                    [22.309196, 60.493336],
                    [22.308259, 60.4937],
                    [22.307417, 60.494012],
                    [22.306937, 60.494182],
                    [22.306443, 60.494348],
                    [22.30568, 60.494597],
                    [22.304983, 60.49482],
                    [22.304693, 60.494903],
                    [22.304345, 60.495002],
                    [22.303642, 60.495193],
                    [22.303402, 60.495258],
                ]
            ],
        },
        "properties": {
            "situationId": "GUID50430207",
            "situationType": "ROAD_WORK",
            "trafficAnnouncementType": None,
            "version": 1,
            "releaseTime": "2024-06-06T05:38:01.991Z",
            "versionTime": "2024-06-06T05:38:01.99Z",
            "announcements": [
                {
                    "language": "FI",
                    "title": "Tie 40, eli Turun kehätie, Turku. Tietyö. ",
                    "location": {
                        "countryCode": 6,
                        "locationTableNumber": 17,
                        "locationTableVersion": "1.11.44",
                        "description": "Tie 40,.. vaikutusalue 1,1 km, suuntaan Kärsämäen risteyssilta.",
                    },
                    "locationDetails": {
                        "roadAddressLocation": {
                            "primaryPoint": {
                                "municipality": "Turku",
                                "province": "Varsinais-Suomi",
                                "country": "Suomi",
                                "roadAddress": {
                                    "road": 40,
                                    "roadSection": 4,
                                    "distance": 2098,
                                },
                                "roadName": "Turun kehätie",
                                "alertCLocation": {
                                    "locationCode": 2676,
                                    "name": "Orikedon risteyssilta",
                                    "distance": 268,
                                },
                            },
                            "secondaryPoint": {
                                "municipality": "Turku",
                                "province": "Varsinais-Suomi",
                                "country": "Suomi",
                                "roadAddress": {
                                    "road": 40,
                                    "roadSection": 4,
                                    "distance": 1025,
                                },
                                "roadName": "Turun kehätie",
                                "alertCLocation": {
                                    "locationCode": 2675,
                                    "name": "Kärsämäen risteyssilta",
                                    "distance": 1025,
                                },
                            },
                            "direction": "NEG",
                            "directionDescription": "Piikkiö",
                        }
                    },
                    "features": [],
                    "roadWorkPhases": [
                        {
                            "id": "GUID50432255",
                            "location": {
                                "countryCode": 6,
                                "locationTableNumber": 17,
                                "locationTableVersion": "1.11.44",
                                "description": "Tie 40, ...vaikutusalue 1,1 km, suuntaan Kärsämäen risteyssilta.",
                            },
                            "locationDetails": {
                                "roadAddressLocation": {
                                    "primaryPoint": {
                                        "municipality": "Turku",
                                        "province": "Varsinais-Suomi",
                                        "country": "Suomi",
                                        "roadAddress": {
                                            "road": 40,
                                            "roadSection": 4,
                                            "distance": 2098,
                                        },
                                        "roadName": "Turun kehätie",
                                        "alertCLocation": {
                                            "locationCode": 2676,
                                            "name": "Orikedon risteyssilta",
                                            "distance": 268,
                                        },
                                    },
                                    "secondaryPoint": {
                                        "municipality": "Turku",
                                        "province": "Varsinais-Suomi",
                                        "country": "Suomi",
                                        "roadAddress": {
                                            "road": 40,
                                            "roadSection": 4,
                                            "distance": 1025,
                                        },
                                        "roadName": "Turun kehätie",
                                        "alertCLocation": {
                                            "locationCode": 2675,
                                            "name": "Kärsämäen risteyssilta",
                                            "distance": 1025,
                                        },
                                    },
                                    "direction": "NEG",
                                    "directionDescription": "Piikkiö",
                                }
                            },
                            "workingHours": [
                                {
                                    "weekday": "TUESDAY",
                                    "startTime": "09:00:00",
                                    "endTime": "15:00:00",
                                }
                            ],
                            "timeAndDuration": {
                                "startTime": "2024-06-10T21:00:00Z",
                                "endTime": "2024-06-11T20:59:59.999Z",
                            },
                            "workTypes": [
                                {"type": "BRIDGE", "description": "Siltatyö"},
                                {"type": "OTHER", "description": ""},
                            ],
                            "restrictions": [
                                {
                                    "type": "SINGLE_LANE_CLOSED",
                                    "restriction": {"name": "Yksi ajokaista suljettu"},
                                },
                                {
                                    "type": "SPEED_LIMIT",
                                    "restriction": {
                                        "name": "Nopeusrajoitus",
                                        "quantity": 60.0,
                                        "unit": "km/h",
                                    },
                                },
                                {
                                    "type": "SPEED_LIMIT_LENGTH",
                                    "restriction": {
                                        "name": "Matka, jolla nopeusrajoitus voimassa",
                                        "quantity": 500.0,
                                        "unit": "m",
                                    },
                                },
                            ],
                            "restrictionsLiftable": True,
                            "severity": "HIGH",
                            "slowTrafficTimes": [],
                            "queuingTrafficTimes": [],
                        }
                    ],
                    "timeAndDuration": {
                        "startTime": "2024-06-10T21:00:00Z",
                        "endTime": "2024-06-11T20:59:59.999Z",
                    },
                    "additionalInformation": "Liikenne- ja kelitiedot verkossa: https://liikennetilanne.fintraffic.fi/",
                    "sender": "Fintraffic Tieliikennekeskus Turku",
                }
            ],
            "contact": {
                "phone": "02002100",
                "email": "turku.liikennekeskus@fintraffic.fi",
            },
            "dataUpdatedTime": "2024-06-06T05:38:04Z",
        },
    }
]

data_outside_southwest_finland = [
    {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [25.693552, 62.190616]},
        "properties": {
            "situationId": "GUID50428325",
            "situationType": "ROAD_WORK",
            "trafficAnnouncementType": None,
            "version": 1,
            "releaseTime": "2024-05-08T07:21:39.52Z",
            "versionTime": "2024-05-08T07:21:39.519Z",
            "announcements": [
                {
                    "language": "FI",
                    "title": "Tie 6110, Jyväskylä. Tietyö. ",
                    "location": {
                        "countryCode": 6,
                        "locationTableNumber": 17,
                        "locationTableVersion": "1.11.43",
                        "description": "Tie 6110 välillä Keljonkangas - Säynätsalo, Jyväskylä.",
                    },
                    "roadWorkPhases": [
                        {
                            "id": "GUID50430172",
                            "location": {
                                "countryCode": 6,
                                "locationTableNumber": 17,
                                "locationTableVersion": "1.11.43",
                                "description": "Tie 6110 välillä Keljonkangas - Säynätsalo, Jyväskylä.",
                            },
                            "locationDetails": {
                                "roadAddressLocation": {
                                    "primaryPoint": {
                                        "municipality": "Jyväskylä",
                                        "province": "Keski-Suomi",
                                        "country": "Suomi",
                                        "roadAddress": {
                                            "road": 6110,
                                            "roadSection": 1,
                                            "distance": 0,
                                        },
                                        "alertCLocation": {
                                            "locationCode": 21413,
                                            "name": "Takakeljon tienhaara",
                                        },
                                    },
                                    "direction": "UNKNOWN",
                                }
                            },
                            "workingHours": [
                                {
                                    "weekday": "TUESDAY",
                                    "startTime": "07:00:00",
                                    "endTime": "16:00:00",
                                },
                                {
                                    "weekday": "MONDAY",
                                    "startTime": "07:00:00",
                                    "endTime": "16:00:00",
                                },
                                {
                                    "weekday": "FRIDAY",
                                    "startTime": "07:00:00",
                                    "endTime": "16:00:00",
                                },
                                {
                                    "weekday": "THURSDAY",
                                    "startTime": "07:00:00",
                                    "endTime": "16:00:00",
                                },
                                {
                                    "weekday": "WEDNESDAY",
                                    "startTime": "07:00:00",
                                    "endTime": "16:00:00",
                                },
                            ],
                            "timeAndDuration": {
                                "startTime": "2024-05-12T21:00:00Z",
                                "endTime": "2024-08-30T20:59:59.999Z",
                            },
                            "workTypes": [
                                {
                                    "type": "OTHER",
                                    "description": "Pysäköintialueen rakentaminen",
                                }
                            ],
                            "restrictions": [],
                            "restrictionsLiftable": False,
                            "severity": "LOW",
                            "slowTrafficTimes": [],
                            "queuingTrafficTimes": [],
                        }
                    ],
                    "timeAndDuration": {
                        "startTime": "2024-05-12T21:00:00Z",
                        "endTime": "2024-08-30T20:59:59.999Z",
                    },
                    "additionalInformation": "Liikenne- ja kelitiedot verkossa: https://liikennetilanne.fintraffic.fi/",
                    "sender": "Fintraffic Tieliikennekeskus Tampere",
                }
            ],
            "contact": {
                "phone": "02002100",
                "email": "tampere.liikennekeskus@fintraffic.fi",
            },
            "dataUpdatedTime": "2024-05-08T07:21:41Z",
        },
    }
]


def import_command(*args, **kwargs):
    out = StringIO()
    call_command(
        "import_traffic_situations",
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
    return out.getvalue()


@pytest.mark.django_db
@freeze_time("2024-06-11 12:00:00", tz_offset=2)
def test_import_traffic_situation():
    import_command(test_importer=data)
    assert SituationType.objects.count() == 1
    assert SituationType.objects.first().type_name == "ROAD_WORK"
    assert Situation.objects.count() == 1
    situation = Situation.objects.first()
    assert situation.situation_id == "GUID50430207"
    assert situation.is_active is True
    assert SituationLocation.objects.count() == 1
    location = SituationLocation.objects.first()
    assert "MULTILINESTRING" in location.geometry.wkt
    assert location.location is None
    assert SituationAnnouncement.objects.count() == 1
    assert location.details["primaryPoint"]["roadName"] == "Turun kehätie"
    announcement = SituationAnnouncement.objects.first()
    assert announcement in situation.announcements.all()
    assert announcement.title == "Tie 40, eli Turun kehätie, Turku. Tietyö. "
    assert "aikutusalue 1,1 km, suuntaan Kärsämäen " in announcement.description
    assert (
        announcement.additional_info["sender"] == "Fintraffic Tieliikennekeskus Turku"
    )
    assert announcement.location == location
    # Test that no duplicates are created
    import_command(test_importer=data)
    assert Situation.objects.count() == 1
    assert SituationType.objects.count() == 1
    assert SituationAnnouncement.objects.count() == 1
    assert SituationLocation.objects.count() == 1


@pytest.mark.django_db
def test_import_traffic_situation_outside_southwest_finland():
    import_command(test_importer=data_outside_southwest_finland)
    assert Situation.objects.count() == 0
    assert SituationType.objects.count() == 0
    assert SituationAnnouncement.objects.count() == 0
    assert SituationLocation.objects.count() == 0
