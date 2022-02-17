from django.core import management
from celery import shared_task

@shared_task
def import_iot_data(source_name, name="Import iot data"):
    print("Source NAME", source_name)
    management.call_command("import_iot_data", source_name)


@shared_task
def import_rent24_cars(name="import rent24 cars"):
    management.call_command("import_iot_data", "R24")


@shared_task
def import_infraroad_snow_plows(name="import infraroad snow plows"):
    management.call_command("import_iot_data", "ISP")
