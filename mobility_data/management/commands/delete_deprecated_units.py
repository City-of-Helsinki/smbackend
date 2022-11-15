from django.core.management import BaseCommand

from mobility_data.models import ContentType


class Command(BaseCommand):
    def handle(self, *args, **options):
        # New model will not have a 'type_name' field.
        ContentType.objects.filter(type_name__isnull=False).delete()
