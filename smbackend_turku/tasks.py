from celery import shared_task
from django.core import management


@shared_task
def turku_services_import(args, name="turku_services_import"):
    management.call_command("turku_services_import", args)


@shared_task
def import_mds_data(name="import_mds_data"):
    management.call_command(
        "turku_services_import", "services", "accessibility", "units"
    )


@shared_task
def import_all_addresses(name="import_all_addresses"):
    # Task that imports all the addresses and indexes search columns
    management.call_command("turku_services_import", "addresses")
    management.call_command("turku_services_import", "enriched_addresses")
    management.call_command("turku_services_import", "geo_search_addresses")
    management.call_command("index_search_columns")


@shared_task
def import_addresses(name="import_addresses"):
    # Imports addresses for Turku and Karina from the WFS server hosted by Turku
    management.call_command("turku_services_import", "addresses")


@shared_task
def geo_import_municipalities(name="geo_import_municipalities"):
    management.call_command("geo_import", "finland", "--municipalities")


@shared_task
def index_search_columns(name="index_search_columns"):
    management.call_command("index_search_columns")


@shared_task
def import_geo_search_addresses(name="import_geo_search_addresses"):
    # Imports the addresses of Southwest Finland(not Turku and Kaarina) from geo-search(paikkatietohaku)
    management.call_command("turku_services_import", "geo_search_addresses")


@shared_task
def import_enriched_addresses(name="import_enriched_addresses"):
    # Enriches addresses for Turku and Karina from geo-search(paikkatietohaku)
    management.call_command("turku_services_import", "enriched_addresses")


@shared_task
def import_bicycle_stands(name="import_bicycle_stands"):
    management.call_command("turku_services_import", "bicycle_stands")


@shared_task
def import_gas_filling_stations(name="import_gas_filling_stations"):
    management.call_command("turku_services_import", "gas_filling_stations")
