import logging

from django.core.management import BaseCommand

from exceptional_situations.models import Situation, SituationAnnouncement

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        num_deleted = 0
        for situation in Situation.objects.all():
            if situation.is_active is False:
                SituationAnnouncement.objects.filter(situation=situation).delete()
                situation.delete()
                num_deleted += 1
        logger.info(f"Deleted {num_deleted} inactive situations.")
