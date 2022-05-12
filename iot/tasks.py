from django.core import management
from celery import shared_task


@shared_task
def import_iot_data(source_name, name="Import iot data"):
    management.call_command("import_iot_data", source_name)
