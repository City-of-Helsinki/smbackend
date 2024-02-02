from django.core import management

from mobility_data.models import ContentType, MobileUnit
from smbackend.utils import shared_task_email


@shared_task_email
def import_culture_routes(args=None, name="import_culture_routes"):
    if args:
        management.call_command("import_culture_routes", args)
    else:
        management.call_command("import_culture_routes")


@shared_task_email
def import_payments_zones(name="import_payment_zones"):
    management.call_command("import_wfs", "PaymentZone")


@shared_task_email
def import_speed_limit_zones(name="import_speed_limit_zones"):
    management.call_command("import_wfs", "SpeedLimitZone")


@shared_task_email
def import_scooter_restrictions(name="import_scooter_restrictions"):
    management.call_command(
        "import_wfs",
        ["ScooterParkingArea", "ScooterSpeedLimitArea", "ScooterNoParkingArea"],
    )


@shared_task_email
def import_mobility_data(name="import_mobility_data"):
    management.call_command("import_mobility_data")


@shared_task_email
def import_accessories(name="import_accessories"):
    management.call_command(
        "import_wfs",
        ["PublicToilet", "PublicTable", "PublicBench", "PublicFurnitureGroup"],
    )


@shared_task_email
def import_barbecue_places(name="import_barbecue_places"):
    management.call_command("import_wfs", ["BarbecuePlace"])


@shared_task_email
def import_playgrounds(name="import_playgrounds"):
    management.call_command("import_wfs", ["PlayGround"])


@shared_task_email
def import_share_car_parking_places(name="impor_share_car_parking_places"):
    management.call_command("import_share_car_parking_places")


@shared_task_email
def import_bicycle_networks(name="import_bicycle_networks"):
    management.call_command(
        "import_wfs", ["BrushSaltedBicycleNetwork", "BrushSandedBicycleNetwork"]
    )


@shared_task_email
def import_marinas(name="import_marinas"):
    management.call_command("import_marinas")


@shared_task_email
def import_foli_stops(name="import_foli_stops"):
    management.call_command("import_foli_stops")


@shared_task_email
def import_foli_parkandride_stops(name="import_foli_parkandride_stops"):
    management.call_command("import_foli_parkandride_stops")


@shared_task_email
def import_outdoor_gym_devices(name="import_outdoor_gym_devices"):
    management.call_command("import_outdoor_gym_devices")


@shared_task_email
def import_disabled_and_no_staff_parkings(name="import_disabled_and_no_staff_parkings"):
    management.call_command("import_disabled_and_no_staff_parkings")


@shared_task_email
def import_loading_and_unloading_places(name="import_loading_and_unloading_places"):
    management.call_command("import_loading_and_unloading_places")


@shared_task_email
def import_lounaistieto_shapefiles(name="import_lounaistieto_shapefiles"):
    management.call_command("import_lounaistieto_shapefiles")


@shared_task_email
def import_paavonpolkus(name="import_paavonpolkus"):
    management.call_command("import_wfs", "PaavonPolku")


@shared_task_email
def import_school_and_kindergarten_accessibility_areas(
    name="import_import_school_and_kindergarten_accessibility_areas",
):
    management.call_command("import_wfs", "SchoolAndKindergartenAccessibilityArea")


@shared_task_email
def delete_mobility_data(args=None, name="delete_mobility_data"):
    management.call_command("delete_mobility_data", args)


@shared_task_email
def import_outdoor_trails(name="import_outdoor_trails"):
    management.call_command(
        "import_wfs", ["PaddlingTrail", "HikingTrail", "NatureTrail", "FitnessTrail"]
    )


@shared_task_email
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


@shared_task_email
def import_wfs(args=None, name="import_wfs"):
    management.call_command("import_wfs", args)


@shared_task_email
def import_parking_machines(name="import_parking_machines"):
    management.call_command("import_parking_machines")


@shared_task_email
def import_under_and_overpasses(name="import_under_and_overpasses"):
    management.call_command("import_under_and_overpasses")


@shared_task_email
def delete_obsolete_data(name="delete_obsolete_data"):
    MobileUnit.objects.filter(content_types__isnull=True).delete()
    ContentType.objects.filter(mobile_units__content_types__isnull=True).delete()


@shared_task_email
def delete_deprecated_units(name="delete_deprecated_units"):
    management.call_command("delete_deprecated_units")
