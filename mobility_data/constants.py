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
}
