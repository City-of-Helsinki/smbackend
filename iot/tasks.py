from django.core import management

from smbackend.utils import shared_task_email


@shared_task_email
def import_iot_data(source_name, name="Import iot data"):
    management.call_command("import_iot_data", source_name)
