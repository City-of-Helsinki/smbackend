import logging
from datetime import datetime

from django.core.management import BaseCommand

from street_maintenance.models import MaintenanceUnit, MaintenanceWork

from .constants import (
    FETCH_SIZE,
    HISTORY_SIZE,
    HISTORY_SIZES,
    PROVIDER_TYPES,
    PROVIDERS,
)
from .utils import (
    create_kuntec_maintenance_units,
    create_kuntec_maintenance_works,
    create_maintenance_units,
    create_maintenance_works,
    create_yit_maintenance_units,
    create_yit_maintenance_works,
    get_yit_access_token,
    precalculate_geometry_history,
)

logger = logging.getLogger("street_maintenance")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--fetch-size",
            type=int,
            nargs="+",
            default=False,
            help=("Max number of location history items to fetch per unit."),
        )
        parser.add_argument(
            "--history-size",
            type=int,
            nargs="+",
            default=False,
            help=("History size in days."),
        )
        parser.add_argument(
            "--providers",
            type=str,
            nargs="+",
            default=False,
            help=", ".join(PROVIDERS),
        )

    def handle(self, *args, **options):
        history_size = None
        fetch_size = None

        if options["history_size"]:
            history_size = options["history_size"]
            history_size = (
                history_size[0] if type(history_size) == list else history_size
            )
        if options["fetch_size"]:
            fetch_size = options["fetch_size"]
            fetch_size = fetch_size[0] if type(fetch_size) == list else fetch_size

        providers = [p.upper() for p in options.get("providers", None)]
        for provider in providers:
            if provider not in PROVIDERS:
                logger.warning(
                    f"Provider {provider} not defined, choices are {', '.join(PROVIDERS)}"
                )
                continue
            start_time = datetime.now()
            history_size = (
                history_size if history_size else HISTORY_SIZES[provider][HISTORY_SIZE]
            )
            fetch_size = (
                fetch_size
                if fetch_size
                else HISTORY_SIZES[provider].get(FETCH_SIZE, None)
            )
            match provider.upper():
                case PROVIDER_TYPES.DESTIA | PROVIDER_TYPES.INFRAROAD:
                    num_created_units, num_del_units = create_maintenance_units(
                        provider
                    )
                    num_created_works, num_del_works = create_maintenance_works(
                        provider, history_size, fetch_size
                    )
                case PROVIDER_TYPES.KUNTEC:
                    num_created_units, num_del_units = create_kuntec_maintenance_units()
                    num_created_works, num_del_works = create_kuntec_maintenance_works(
                        history_size
                    )

                case PROVIDER_TYPES.YIT:
                    access_token = get_yit_access_token()
                    num_created_units, num_del_units = create_yit_maintenance_units(
                        access_token
                    )
                    num_created_works, num_del_works = create_yit_maintenance_works(
                        access_token, history_size
                    )

            tot_num_units = MaintenanceUnit.objects.filter(provider=provider).count()
            tot_num_works = MaintenanceWork.objects.filter(
                maintenance_unit__provider=provider
            ).count()
            logger.info(
                f"Deleted {num_del_units} obsolete Units for provider {provider}"
            )
            logger.info(
                f"Created {num_created_units} units of total {tot_num_units} units for provider {provider}"
            )
            logger.info(
                f"Deleted {num_del_works} obsolete Works for provider {provider}"
            )
            logger.info(
                f"Created {num_created_works} Works of total {tot_num_works} Works for provider {provider}"
            )

            if num_created_works > 0:
                precalculate_geometry_history(provider)
            else:
                logger.warning(
                    f"No works created for {provider}, skipping geometry history population."
                )
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(
                f"Imported {provider} street maintenance history in: {duration}"
            )
