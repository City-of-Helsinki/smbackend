from django.core import management

from smbackend.utils import shared_task_email


@shared_task_email
def import_counter_data(args, name="import_counter_data"):
    management.call_command("import_counter_data", "--counters", args)


@shared_task_email
def initial_import_counter_data(args, name="initial_import_counter_data"):
    management.call_command("import_counter_data", "--init", args)


@shared_task_email
def import_telraam_to_csv(args, name="import_telraam_to_csv"):
    management.call_command("import_telraam_to_csv", args)
