from celery import shared_task
from django.core import management


@shared_task
def import_counter_data(args, name="import_counter_data"):
    management.call_command("import_counter_data", "--counters", args)


@shared_task
def initial_import_counter_data(args, name="initial_import_counter_data"):
    management.call_command("import_counter_data", "--init", args)
