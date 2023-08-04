from django.core.management import BaseCommand

from mobility_data.models import ContentType, GroupType

"""
This command removes all units that have a ContentType or
GroupType where type_name is not Null. This data is deprecated
as only the name will be used in future.
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        ContentType.objects.filter(type_name__isnull=False).delete()
        GroupType.objects.filter(type_name__isnull=False).delete()
