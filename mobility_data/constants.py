from mobility_data.models import ContentType

DATA_SOURCE_IMPORTERS = {
    ContentType.CHARGING_STATION: {
        "importer_name": "charging_stations",
        "to_services_list": True,
    },
    ContentType.BIKE_SERVICE_STATION: {
        "importer_name": "bike_service_stations",
        "to_services_list": True,
    },
    ContentType.SHARE_CAR_PARKING_PLACE: {
        "importer_name": "car_share_parking_places",
        "to_services_list": False,
    },
    ContentType.NO_STAFF_PARKING: {
        "importer_name": "no_staff_parkings",
        "to_services_list": False,
    },
    ContentType.BERTH: {
        "importer_name": "marinas",
        # Uses the marinas importer, but the data contains berths so define
        # optional display_name that is shown to the user instead of the importer name.
        "display_name": "berhts",
        "to_services_list": False,
    },
}
