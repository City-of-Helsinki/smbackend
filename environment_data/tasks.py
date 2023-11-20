from django.core import management

from smbackend.utils import shared_task_email


@shared_task_email
def initial_import(args, name="initial_import"):
    management.call_command("import_environment_data", "--initial-import", args)


@shared_task_email
def initial_import_with_stations(args, name="initial_import_with_stations"):
    management.call_command(
        "import_environment_data", "--initial-import-with-stations", args
    )


@shared_task_email
def incremental_import(args, name="incremental_import"):
    management.call_command("import_environment_data", "--data-types", args)


@shared_task_email
def delete_all_data(name="delete_all_environment_data"):
    management.call_command("delete_all_environment_data")
