from mobility_data.importers.berths import CONTENT_TYPE_NAME as BERTH
from mobility_data.importers.bike_service_stations import (
    CONTENT_TYPE_NAME as BIKE_SERVICE_STATION,
)
from mobility_data.importers.charging_stations import (
    CONTENT_TYPE_NAME as CHARGING_STATION,
)
from mobility_data.importers.disabled_and_no_staff_parking import (
    DISABLED_PARKING_CONTENT_TYPE_NAME as DISABLED_PARKING,
    NO_STAFF_PARKING_CONTENT_TYPE_NAME as NO_STAFF_PARKING,
)
from mobility_data.importers.loading_unloading_places import (
    CONTENT_TYPE_NAME as LOADING_UNLOADING_PLACE,
)
from mobility_data.importers.parking_garages import CONTENT_TYPE_NAME as PARKING_GARAGE
from mobility_data.importers.parking_machines import (
    CONTENT_TYPE_NAME as PARKING_MACHINE,
)
from mobility_data.importers.share_car_parking_places import (
    CONTENT_TYPE_NAME as SHARE_CAR_PARKING_PLACE,
)

DATA_SOURCE_IMPORTERS = {
    CHARGING_STATION: {
        "importer_name": "charging_stations",
        "to_services_list": True,
    },
    BIKE_SERVICE_STATION: {
        "importer_name": "bike_service_stations",
        "to_services_list": True,
    },
    SHARE_CAR_PARKING_PLACE: {
        "importer_name": "share_car_parking_places",
        "to_services_list": False,
    },
    NO_STAFF_PARKING: {
        "importer_name": "disabled_and_no_staff_parkings",
        "to_services_list": False,
    },
    DISABLED_PARKING: {
        "importer_name": "disabled_and_no_staff_parkings",
        "to_services_list": False,
    },
    LOADING_UNLOADING_PLACE: {
        "importer_name": "loading_and_unloading_places",
        "to_services_list": False,
    },
    BERTH: {
        "importer_name": "marinas",
        # Uses the marinas importer, but the data contains berths so define
        # optional display_name that is shown to the user instead of the importer name.
        "display_name": "berths",
        "to_services_list": False,
    },
    PARKING_MACHINE: {
        "importer_name": "parking_machines",
        "to_services_list": False,
    },
    PARKING_GARAGE: {
        "importer_name": "parking_garages",
        "to_services_list": False,
    },
}
