from celery import shared_task
from django.core import management


@shared_task
def import_culture_routes(args=None, name="import_culture_routes"):
    if args:
        management.call_command("import_culture_routes", args)
    else:
        management.call_command("import_culture_routes")


@shared_task
def import_payments_zones(name="import_payment_zones"):
    management.call_command("import_payment_zones")


@shared_task
def import_speed_limit_zones(name="import_speed_limit_zones"):
    management.call_command("import_speed_limit_zones")


@shared_task
def import_scooter_restrictions(name="import_scooter_restrictions"):
    management.call_command("import_scooter_restrictions")


@shared_task
def import_mobility_data(name="import_mobility_data"):
    management.call_command("import_mobility_data")


@shared_task
def import_accessories(name="import_accessories"):
    management.call_command("import_accessories")
