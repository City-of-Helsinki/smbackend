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
    management.call_command("import_wfs", "PaymentZone")


@shared_task
def import_speed_limit_zones(name="import_speed_limit_zones"):
    management.call_command("import_wfs", "SpeedLimitZone")


@shared_task
def import_scooter_restrictions(name="import_scooter_restrictions"):
    management.call_command(
        "import_wfs",
        ["ScooterParkingArea", "ScooterSpeedLimitArea", "ScooterNoParkingArea"],
    )


@shared_task
def import_mobility_data(name="import_mobility_data"):
    management.call_command("import_mobility_data")


@shared_task
def import_accessories(name="import_accessories"):
    management.call_command(
        "import_wfs",
        ["PublicToilet", "PublicTable", "PublicBench", "PublicFurnitureGroup"],
    )


@shared_task
def import_share_car_parking_places(name="impor_share_car_parking_places"):
    management.call_command("import_share_car_parking_places")


@shared_task
def import_bicycle_networks(name="import_bicycle_networks"):
    management.call_command(
        "import_wfs", ["BrushSaltedBicycleNetwork", "BrushSandedBicycleNetwork"]
    )


@shared_task
def import_marinas(name="import_marinas"):
    management.call_command("import_marinas")


@shared_task
def import_foli_stops(name="import_foli_stops"):
    management.call_command("import_foli_stops")


@shared_task
def import_outdoor_gym_devices(name="import_outdoor_gym_devices"):
    management.call_command("import_outdoor_gym_devices")


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
    management.call_command("import_wfs", "PaavonPolku")


@shared_task
def delete_mobility_data(args=None, name="delete_mobility_data"):
    management.call_command("delete_mobility_data", args)


@shared_task
def import_outdoor_trails(name="import_outdoor_trails"):
    management.call_command(
        "import_wfs", ["PaddlingTrail", "HikingTrail", "NatureTrail", "FitnessTrail"]
    )


@shared_task
def import_traffic_signs(name="import_traffic_signs"):
    management.call_command(
        "import_wfs",
        [
            "CrossWalkSign",
            "DisabledParkingSign",
            "ParkingTerminalSign",
            "LocalTrafficBusStopSign",
            "LongDistanceBusStopSign",
            "ParkingForbiddenSign",
            "ParkingForbiddenAreaSign",
            "ObligationToUseParkingDiscSign",
            "PaidParkingSign",
            "ParkingLotSign",
            "RailwayLevelCrossingWithoutBoomsSign",
            "RailwayLevelCrossingWithBoomsSign",
            "SingleTrackRailwayLevelCrossingSign",
            "TicketMachineSign",
            "RouteForDisabledSign",
        ],
    )


@shared_task
def import_wfs(args=None, name="import_wfs"):
    management.call_command("import_wfs", args)


@shared_task
def delete_deprecated_units(name="delete_deprecated_units"):
    management.call_command("delete_deprecated_units")
