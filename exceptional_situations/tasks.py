from django.core import management

from smbackend.utils import shared_task_email


@shared_task_email
def import_traffic_situations(name="import_traffic_situations"):
    management.call_command("import_traffic_situations")


@shared_task_email
def delete_inactive_situations(name="delete_inactive_situations"):
    management.call_command("delete_inactive_situations")


@shared_task_email
def delete_all_situations(name="delete_all_situations"):
    management.call_command("delete_all_situations")
