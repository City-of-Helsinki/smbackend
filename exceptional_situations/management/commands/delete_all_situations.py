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
        SituationLocation.objects.all().delete()
        SituationAnnouncement.objects.all().delete()
        Situation.objects.all().delete()
        logger.info("Deleted all situations.")
