import logging

from django.core.management.base import BaseCommand
from munigeo.models import Address, AdministrativeDivision

from services.models import Service, ServiceNode, Unit

logger = logging.getLogger("services.management")

MODELS = [Address, AdministrativeDivision, Unit, Service, ServiceNode]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logger.info("Emptying search columns...")
        for model in MODELS:
            for lang in ["fi", "sv", "en"]:
                logger.info(
                    f"Emptying search columns for model: {model.__name__} and language"
                    " {lang}."
                )
                key = "search_column_%s" % lang
                model.objects.update(**{key: None})
