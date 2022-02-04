from django.core import management
from celery import shared_task



@shared_task
def import_mds_data(name="import_mds_data"):
    management.call_command("turku_services_import", "services", "accessibility", "units", "addresses")

@shared_task
def import_bicycle_stands(name="import_bicycle_stands"):
    management.call_command("turku_services_import", "bicycle_stands")

@shared_task
def import_gas_filling_stations(name="import_gas_filling_stations"):
    management.call_command("turku_services_import", "gas_filling_stations")

@shared_task
def import_charging_stations(name="import_charging_stations"):
    management.call_command("turku_services_import", "charging_stations")