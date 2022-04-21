from celery import shared_task
from django.core import management


@shared_task
def import_culture_routes(args, name="import_culture_routes"):
    management.call_command("import_culture_routes", args)


@shared_task
def import_payments_zones(name="import_payment_zones"):
    management.call_command("import_payment_zones")
