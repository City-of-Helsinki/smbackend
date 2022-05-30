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
}
