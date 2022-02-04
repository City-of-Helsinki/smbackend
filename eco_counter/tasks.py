
from django.core import management
from celery import shared_task

@shared_task
def import_eco_counter(name="import_eco_counter"):
    management.call_command("import_eco_counter")
  