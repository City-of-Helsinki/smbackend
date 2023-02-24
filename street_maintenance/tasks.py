from django.core import management

from smbackend.utils import shared_task_email


@shared_task_email
def delete_street_maintenance_history(args, name="delete_street_maintenance_history"):
    management.call_command("delete_street_maintenance_history", args)


@shared_task_email
def import_street_maintenance_history(
    name="import_street_maintenance_history", *args, **kwargs
):
    if "providers" not in kwargs:
        raise Exception(
            "No 'providers' item in kwargs. e.g., {'providers':['destia', 'infraroad']}"
        )
    if "fetch-size" not in kwargs:
        kwargs["fetch-size"] = None
    if "history-size" not in kwargs:
        kwargs["history-size"] = None
    management.call_command(
        "import_street_maintenance_history",
        providers=kwargs["providers"],
        fetch_size=kwargs["fetch-size"],
        history_size=kwargs["history-size"],
    )
