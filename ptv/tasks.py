from django.core import management

from smbackend.utils import shared_task_email


@shared_task_email
def import_ptv_data(name="import_ptv_data"):
    # Note, Aura=19 has been removed, thus it is not found in palvelutietovaranto.
    management.call_command(
        "ptv_import",
        "202",
        "284",
        "304",
        "322",
        "400",
        "423",
        "430",
        "445",
        "480",
        "481",
        "529",
        "538",
        "561",
        "577",
        "631",
        "636",
        "680",
        "704",
        "734",
        "738",
        "761",
        "833",
        "853",
        "895",
        "918",
    )
