from celery import shared_task
from django.core import management


@shared_task
def delete_street_maintenance_history(
    args=None, name="delete_street_maintenance_history"
):
    management.call_command("delete_street_maintenance_history", args)


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
def import_yit_street_maintenance_history(
    args=None, name="import_yit_street_maintenance_history"
):
    if args:
        management.call_command(
            "import_yit_street_maintenance_history", "--history-size", args
        )
    else:
        management.call_command("import_yit_street_maintenance_history")


@shared_task
def import_kuntec_street_maintenance_history(
    args=None, name="import_kuntec_street_maintenance_history"
):
    if args:
        management.call_command(
            "import_kuntec_street_maintenance_history", "--history-size", args
        )
    else:
        management.call_command("import_kuntec_street_maintenance_history")


@shared_task
def import_destia_street_maintenance_history(
    args=None, name="import_destia_street_maintenance_history"
):
    if args:
        management.call_command(
            "import_destia_maintenance_history", "--history-size", args
        )
    else:
        management.call_command("import_destia_street_maintenance_history")
