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
    management.call_command("import_wfs", "PAZ")


@shared_task
def import_speed_limit_zones(name="import_speed_limit_zones"):
    management.call_command("import_wfs", "SLZ")


@shared_task
def import_scooter_restrictions(name="import_scooter_restrictions"):
    management.call_command("import_wfs", ["SPG", "SSL", "SNP"])


@shared_task
def import_mobility_data(name="import_mobility_data"):
    management.call_command("import_mobility_data")


@shared_task
def import_accessories(name="import_accessories"):
    management.call_command("import_wfs", ["APT", "ATE", "ABH", "AFG"])


@shared_task
def import_share_car_parking_places(name="impor_share_car_parking_places"):
    management.call_command("import_share_car_parking_places")


@shared_task
def import_bicycle_networks(name="import_bicycle_networks"):
    management.call_command("import_wfs", ["BLB", "BND"])


@shared_task
def import_marinas(name="import_marinas"):
    management.call_command("import_marinas")


@shared_task
def import_disabled_and_no_staff_parkings(name="import_disabled_and_no_staff_parkings"):
    management.call_command("import_disabled_and_no_staff_parkings")


@shared_task
def import_loading_and_unloading_places(name="import_loading_and_unloading_places"):
    management.call_command("import_loading_and_unloading_places")


@shared_task
def import_lounaistieto_shapefiles(name="import_lounaistieto_shapefiles"):
    management.call_command("import_lounaistieto_shapefiles")


@shared_task
def import_paavonpolkus(name="import_paavonpolkus"):
    management.call_command("import_wfs", "PPU")


@shared_task
def delete_mobility_data(args=None, name="delete_mobility_data"):
    management.call_command("delete_mobility_data", args)


@shared_task
def import_outdoor_trails(args=None, name="import_outdoor_trails"):
    management.call_command("import_wfs", ["PTL", "NTL", "HTL", "FTL"])


@shared_task
def import_wfs(args=None, name="import_wfs"):
    management.call_command("import_wfs", args)
