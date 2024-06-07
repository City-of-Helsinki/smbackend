import logging

from django.core.management import BaseCommand

from exceptional_situations.models import (
    Situation,
    SituationAnnouncement,
    SituationLocation,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for situation in Situation.objects.all():
            SituationAnnouncement.objects.filter(situation=situation).delete()
            situation.delete()
            SituationLocation.objects.all().delete()
        logger.info("Deleted all situations.")
