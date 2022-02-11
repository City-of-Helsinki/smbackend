
from django.core import management
from celery import shared_task

@shared_task
def import_culture_routes(name="import_culture_routes"):
    management.call_command("import_culture_routes")
