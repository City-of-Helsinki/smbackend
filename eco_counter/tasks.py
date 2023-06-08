from django.core import management

from smbackend.utils import shared_task_email


@shared_task_email
def import_counter_data(args, name="import_counter_data"):
    management.call_command("import_counter_data", "--counters", args)


@shared_task_email
def initial_import_counter_data(args, name="initial_import_counter_data"):
    management.call_command("import_counter_data", "--init", args)


@shared_task_email
def delete_all_counter_data(name="delete_all_counter_data"):
    management.call_command("delete_all_counter_data")


@shared_task_email
def import_telraam_to_csv(*args, name="import_telraam_to_csv"):
    if args:
        management.call_command("import_telraam_to_csv", args)
    else:
        management.call_command("import_telraam_to_csv")
