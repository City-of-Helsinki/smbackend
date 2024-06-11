"""
Imports road works and traffic announcements in Southwest Finland from digitraffic.fi.
"""

import logging
from copy import deepcopy
from datetime import datetime

import requests
from dateutil import parser
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.core.management import BaseCommand
from django.utils import timezone

from exceptional_situations.models import (
    PROJECTION_SRID,
    Situation,
    SituationAnnouncement,
    SituationLocation,
    SituationType,
)
from mobility_data.importers.constants import (
    SOUTHWEST_FINLAND_BOUNDARY,
    SOUTHWEST_FINLAND_BOUNDARY_SRID,
)

logger = logging.getLogger(__name__)
ROAD_WORK_URL = (
    "https://tie.digitraffic.fi/api/traffic-message/v1/messages"
    "?inactiveHours=0&includeAreaGeometry=true&situationType=ROAD_WORK"
)
TRAFFIC_ANNOUNCEMENT_URL = (
    "https://tie.digitraffic.fi/api/traffic-message/v1/messages"
    "?inactiveHours=0&includeAreaGeometry=true&situationType=TRAFFIC_ANNOUNCEMENT"
)
URLS = [ROAD_WORK_URL, TRAFFIC_ANNOUNCEMENT_URL]
DATETIME_FORMATS = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]

SOUTHWEST_FINLAND_POLYGON = Polygon(
    SOUTHWEST_FINLAND_BOUNDARY, srid=SOUTHWEST_FINLAND_BOUNDARY_SRID
)


def get_or_create(model, filter):
    obj = model.objects.filter(**filter).first()
    if obj:
        return obj
    else:
        return model.objects.create(**filter)


class Command(BaseCommand):
    def get_geos_geometry(self, feature_data):
        return GEOSGeometry(str(feature_data["geometry"]), srid=PROJECTION_SRID)

    def create_location(self, geometry, announcement_data):
        location = None
        details = announcement_data["locationDetails"].get("roadAddressLocation", None)
        if details:
            details.update(announcement_data.get("location", None))
        filter = {
            "geometry": geometry,
            "location": location,
            "details": details,
        }
        return get_or_create(SituationLocation, filter)

    def create_announcement(self, announcement_data, location):
        title = announcement_data.get("title", "")
        description = announcement_data["location"].get("description", "")
        additional_info = {}
        for road_work_phase in announcement_data.get("roadWorkPhases", []):
            del road_work_phase["locationDetails"]
            del road_work_phase["location"]
            additional_info.update(road_work_phase)

        additional_info.update(
            {
                "additionalInformation": announcement_data.get(
                    "additionalInformation", None
                )
            }
        )
        additional_info.update({"sender": announcement_data.get("sender", None)})
        start_time = parser.parse(
            announcement_data["timeAndDuration"].get("startTime", None)
        )
        end_time = announcement_data["timeAndDuration"].get("endTime", None)
        # Note, endTime can be None (unknown)
        if end_time:
            end_time = parser.parse(end_time)
        filter = {
            "title": title,
            "description": description,
            "additional_info": additional_info,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
        }
        return get_or_create(SituationAnnouncement, filter)

    def save_features(self, features):
        num_imported = 0
        for feature_data in features:
            geometry = self.get_geos_geometry(feature_data)
            if not SOUTHWEST_FINLAND_POLYGON.intersects(geometry):
                continue

            properties = feature_data.get("properties", None)
            if not properties:
                continue
            situation_id = properties.get("situationId", None)
            release_time_str = properties.get("releaseTime", None)
            if release_time_str:
                for format_str in DATETIME_FORMATS:
                    try:
                        release_time = datetime.strptime(release_time_str, format_str)
                    except ValueError:
                        pass
                    else:
                        break

                if release_time.microsecond != 0:
                    release_time.replace(microsecond=0)
                release_time = timezone.make_aware(release_time, timezone.utc)

            type_name = properties.get("situationType", None)
            sub_type_name = properties.get("trafficAnnouncementType", None)

            situation_type, _ = SituationType.objects.get_or_create(
                type_name=type_name, sub_type_name=sub_type_name
            )

            filter = {
                "situation_id": situation_id,
                "situation_type": situation_type,
            }
            situation, created = Situation.objects.get_or_create(**filter)
            situation.release_time = release_time
            situation.save()
            if not created:
                SituationAnnouncement.objects.filter(situation=situation).delete()
                situation.announcements.clear()
            for announcement_data in properties.get("announcements", []):
                situation_location = self.create_location(geometry, announcement_data)
                situation_announcement = self.create_announcement(
                    deepcopy(announcement_data), situation_location
                )
                situation.announcements.add(situation_announcement)
            num_imported += 1
        return num_imported

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-importer",
            type=list,
            default=[],
            nargs="*",
            help="Test importing of data.",
        )

    def handle(self, *args, **options):
        num_imported = 0
        if options.get("test_importer", False):
            features = [options["test_importer"][0]]
            self.save_features(features)
        else:
            for url in URLS:
                try:
                    response = requests.get(url)
                    assert response.status_code == 200
                except AssertionError:
                    continue
                features = response.json()["features"]
                num_imported += self.save_features(features)
            logger.info(f"Imported/updated {num_imported} traffic situations.")
