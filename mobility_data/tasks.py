from celery import shared_task
from django.core import management


@shared_task
def import_culture_routes(args, name="import_culture_routes"):
    management.call_command("import_culture_routes", args)
