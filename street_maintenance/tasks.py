from celery import shared_task
from django.core import management


@shared_task
def import_infraroad_street_maintenance_history(
    args=None, name="import_infraroad_street_maintenance_history"
):
    if args:
        management.call_command(
            "import_infraroad_street_maintenance_history", "--history-size", args
        )
    else:
        management.call_command("import_infraroad_street_maintenance_history")


@shared_task
def import_autori_street_maintenance_history(
    args=None, name="import_autori_street_maintenance_history"
):
    if args:
        management.call_command(
            "import_autori_street_maintenance_history", "--history-size", args
        )
    else:
        management.call_command("import_autori_street_maintenance_history")
