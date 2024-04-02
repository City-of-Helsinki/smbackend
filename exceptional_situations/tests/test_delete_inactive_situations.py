import pytest
from django.core.management import call_command

from exceptional_situations.models import Situation, SituationAnnouncement


@pytest.mark.django_db
def test_delete_inactive_situations(inactive_situations, inactive_announcements):
    assert Situation.objects.count() == 1
    assert SituationAnnouncement.objects.count() == 1
    call_command("delete_inactive_situations")
    assert Situation.objects.count() == 0
    assert SituationAnnouncement.objects.count() == 0
