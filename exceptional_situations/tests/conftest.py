from datetime import datetime, timedelta

import pytest
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone
from munigeo.models import Municipality
from rest_framework.test import APIClient

from exceptional_situations.models import (
    Situation,
    SituationAnnouncement,
    SituationLocation,
    SituationType,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def now():
    return datetime.now().replace(tzinfo=timezone.get_default_timezone())


@pytest.mark.django_db
@pytest.fixture
def municipalities():
    Municipality.objects.create(id="turku", name="Turku")
    Municipality.objects.create(id="lieto", name="Lieto")
    Municipality.objects.create(id="raisio", name="Raisio")
    return Municipality.objects.all()


@pytest.mark.django_db
@pytest.fixture
def situation_types():
    SituationType.objects.create(
        type_name="test type name", sub_type_name="test sub type name"
    )
    return SituationType.objects.all()


@pytest.mark.django_db
@pytest.fixture
def locations():
    json_data = {"test_key": "test_value"}
    SituationLocation.objects.create(
        details=json_data, geometry=GEOSGeometry("POINT(0 0)")
    )
    SituationLocation.objects.create(
        details=json_data, geometry=GEOSGeometry("POINT(1 0)")
    )
    SituationLocation.objects.create(
        details=json_data, geometry=GEOSGeometry("POINT(0 1)")
    )

    return SituationLocation.objects.all()


@pytest.mark.django_db
@pytest.fixture
def announcements(locations, municipalities, now):

    json_data = {"test_key": "test_value"}
    sa = SituationAnnouncement.objects.create(
        title="Twelve hours",
        description="Twelve hours long situation",
        additional_info=json_data,
        location=locations[0],
        start_time=now,
        end_time=now + timedelta(hours=12),
    )
    sa.municipalities.add(municipalities.filter(id="turku").first())
    sa.municipalities.add(municipalities.filter(id="lieto").first())
    sa = SituationAnnouncement.objects.create(
        title="two days",
        description="two days long situation",
        additional_info=json_data,
        location=locations[1],
        start_time=now - timedelta(days=1),
        end_time=now + timedelta(days=1),
    )
    sa.municipalities.add(municipalities.filter(id="raisio").first())
    return SituationAnnouncement.objects.all()


@pytest.mark.django_db
@pytest.fixture
def inactive_announcements(locations, now):
    json_data = {"test_key": "test_value"}
    SituationAnnouncement.objects.create(
        title="in past",
        description="inactive announcement",
        additional_info=json_data,
        location=locations[2],
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(days=1),
    )
    return SituationAnnouncement.objects.all()


@pytest.mark.django_db
@pytest.fixture
def inactive_situations(situation_types, inactive_announcements, now):
    situation = Situation.objects.create(
        release_time=now,
        situation_id="inactive",
        situation_type=situation_types.first(),
    )
    situation.announcements.add(inactive_announcements.first())
    return Situation.objects.all()


@pytest.mark.django_db
@pytest.fixture
def situations(situation_types, announcements, now):
    situation = Situation.objects.create(
        release_time=now,
        situation_id="TwelveHoursLong",
        situation_type=situation_types.first(),
    )
    situation.announcements.add(announcements[0])
    situation = Situation.objects.create(
        release_time=now - timedelta(days=1),
        situation_id="TwoDaysLong",
        situation_type=situation_types.first(),
    )
    situation.announcements.add(announcements[1])
    return Situation.objects.all()
