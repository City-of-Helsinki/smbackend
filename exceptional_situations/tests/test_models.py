from datetime import timedelta

import pytest

from exceptional_situations.models import Situation, SituationAnnouncement


@pytest.mark.django_db
def test_situation_is_active(situation_types, now):

    announcement_1 = SituationAnnouncement.objects.create(start_time=now, title="test1")
    announcement_2 = SituationAnnouncement.objects.create(start_time=now, title="test2")
    situation = Situation.objects.create(
        release_time=now, situation_type=situation_types.first(), situation_id="TestID"
    )
    # No announcements, returns False
    assert situation.is_active is False

    situation.announcements.add(announcement_1)
    situation.announcements.add(announcement_2)
    assert situation.is_active is True

    announcement_1.start_time = now - timedelta(days=2)
    announcement_1.end_time = now - timedelta(days=1)
    announcement_1.save()
    announcement_2.start_time = now - timedelta(hours=2)
    announcement_2.end_time = now - timedelta(hours=1)
    announcement_2.save()
    assert situation.is_active is False

    announcement_2.start_time = now - timedelta(hours=2)
    announcement_2.end_time = now + timedelta(hours=1)
    announcement_2.save()
    assert situation.is_active is True
    # Test that returns False if all start times are in future
    announcement_1.start_time = now + timedelta(days=2)
    announcement_1.end_time = now + timedelta(days=3)
    announcement_1.save()
    announcement_2.start_time = now + timedelta(hours=2)
    announcement_2.end_time = now + timedelta(hours=3)
    announcement_2.save()
    assert situation.is_active is False


@pytest.mark.django_db
def test_situation_start_time(situation_types, now):
    announcement_1 = SituationAnnouncement.objects.create(
        start_time=now, title="starts now"
    )
    announcement_2 = SituationAnnouncement.objects.create(
        start_time=now - timedelta(hours=1), title="started an hour ago"
    )
    situation = Situation.objects.create(
        release_time=now, situation_type=situation_types.first(), situation_id="TestID"
    )
    situation.announcements.add(announcement_1)
    situation.announcements.add(announcement_2)
    assert situation.start_time == announcement_2.start_time


@pytest.mark.django_db
def test_situation_end_time(situation_types, now):
    announcement_1 = SituationAnnouncement.objects.create(
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        title="ends after two hours",
    )
    announcement_2 = SituationAnnouncement.objects.create(
        start_time=now, end_time=now + timedelta(days=2), title="ends after two days"
    )
    situation = Situation.objects.create(
        release_time=now, situation_type=situation_types.first(), situation_id="TestID"
    )
    situation.announcements.add(announcement_1)
    situation.announcements.add(announcement_2)
    assert situation.end_time == announcement_2.end_time
    assert situation.start_time == announcement_1.start_time
