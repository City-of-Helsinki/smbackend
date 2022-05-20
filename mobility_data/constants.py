from mobility_data.models import ContentType

DATA_SOURCE_IMPORTERS = {
    ContentType.CHARGING_STATION: {
        "importer_name": "charging_stations",
        "to_services_list": True,
    },
}
