import logging

from django.core.management import BaseCommand

from street_maintenance.models import GeometryHistory, MaintenanceUnit

from .constants import PROVIDERS

logger = logging.getLogger("mobility_data")

# Add deprecated provider name 'AUTORI'
PROVIDERS.append("AUTORI")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "providers",
            type=str,
            nargs="*",
            help=", ".join(PROVIDERS),
        )

    def handle(self, *args, **options):
        providers = [p.upper() for p in options.get("providers", None)]

        for provider in providers:
            if provider not in PROVIDERS:
                logger.error(
                    f"Invalid providers argument {provider}, choices are: {', '.join(PROVIDERS)}"
                )
                continue

            logger.info(f"Deleting street maintenance history for {provider}.")
            provider = provider.upper()
            deleted_units = MaintenanceUnit.objects.filter(provider=provider).delete()
            deleted_histories = GeometryHistory.objects.filter(
                provider=provider
            ).delete()
            if "street_maintenance.MaintenanceUnit" in deleted_units[1]:
                num_deleted_units = deleted_units[1][
                    "street_maintenance.MaintenanceUnit"
                ]
            else:
                num_deleted_units = 0
            if "street_maintenance.MaintenanceWork" in deleted_units[1]:
                num_deleted_works = deleted_units[1][
                    "street_maintenance.MaintenanceWork"
                ]
            else:
                num_deleted_works = 0
            if "street_maintenance.GeometryHistory" in deleted_histories[1]:
                num_deleted_histories = deleted_histories[1][
                    "street_maintenance.GeometryHistory"
                ]
            else:
                num_deleted_histories = 0

            logger.info(f"GeometryHistorys deleted {num_deleted_histories}.")
            logger.info(f"MaintenanceUnits deleted {num_deleted_units}.")
            logger.info(f"MaintenanceWorks deleted {num_deleted_works}.")
