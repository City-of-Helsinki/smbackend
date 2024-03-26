"""
Imports road works and traffic announcements in Southwest Finland from digitraffic.fi.
"""

import logging
from copy import deepcopy

import requests
from dateutil import parser
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.core.management import BaseCommand

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
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SOUTHWEST_FINLAND_POLYGON = Polygon(
    SOUTHWEST_FINLAND_BOUNDARY, srid=SOUTHWEST_FINLAND_BOUNDARY_SRID
)


class Command(BaseCommand):
    def get_geos_geometry(self, feature_data):
        return GEOSGeometry(str(feature_data["geometry"]), srid=PROJECTION_SRID)

    def create_location(self, geometry, announcement_data):
        location = None
        details = announcement_data["locationDetails"].get("roadAddressLocation", None)
        details.update(announcement_data.get("location", None))
        filter = {
            "geometry": geometry,
            "location": location,
            "details": details,
        }
        situation_location = SituationLocation.objects.create(**filter)
        return situation_location

    def create_announcement(self, announcement_data, situation_location):
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
            "location": situation_location,
            "title": title,
            "description": description,
            "additional_info": additional_info,
            "start_time": start_time,
            "end_time": end_time,
        }
        situation_announcement = SituationAnnouncement.objects.create(**filter)
        return situation_announcement

    def handle(self, *args, **options):
        num_imported = 0
        for url in URLS:
            try:
                response = requests.get(url)
                assert response.status_code == 200
            except AssertionError:
                continue
            features = response.json()["features"]

            for feature_data in features:
                geometry = self.get_geos_geometry(feature_data)
                if not SOUTHWEST_FINLAND_POLYGON.intersects(geometry):
                    continue

                properties = feature_data.get("properties", None)
                if not properties:
                    continue
                situation_id = properties.get("situationId", None)
                release_time = properties.get("releaseTime", None)
                try:
                    release_time = parser.parse(release_time)
                except parser.ParserError:
                    logger.error(f"Invalid release time {release_time}")
                    continue

                type_name = properties.get("situationType", None)
                sub_type_name = properties.get("trafficAnnouncementType", None)

                situation_type, _ = SituationType.objects.get_or_create(
                    type_name=type_name, sub_type_name=sub_type_name
                )

                filter = {
                    "situation_id": situation_id,
                    "release_time": release_time,
                    "situation_type": situation_type,
                }
                situation, _ = Situation.objects.get_or_create(**filter)

                SituationLocation.objects.filter(situation=situation).delete()
                SituationAnnouncement.objects.filter(situation=situation).delete()
                situation.locations.clear()
                situation.announcements.clear()
                for announcement_data in properties.get("announcements", []):
                    situation_location = self.create_location(
                        geometry, announcement_data
                    )
                    situation.locations.add(situation_location)
                    situation_announcement = self.create_announcement(
                        deepcopy(announcement_data), situation_location
                    )
                    situation.announcements.add(situation_announcement)
                num_imported += 1
        logger.info(f"Imported/updated {num_imported} traffic situations.")
