import logging
import os

import yaml
from django.core.management import BaseCommand

from mobility_data.importers.utils import get_root_dir
from mobility_data.importers.wfs import import_wfs_feature

logger = logging.getLogger("mobility_data")

CONFIG_FILE = "wfs_importer_config.yml"


def get_yaml_config():
    config_path = f"{get_root_dir()}/mobility_data/importers/data/"
    path = os.path.join(config_path, CONFIG_FILE)
    return yaml.safe_load(open(path, "r", encoding="utf-8"))


def get_configured_cotent_types(config=None):
    if not config:
        config = get_yaml_config()
    return [f["content_type"] for f in config["features"]]


class Command(BaseCommand):
    config = get_yaml_config()

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-mode",
            nargs="+",
            default=False,
            help="Run script in test mode.",
        )
        # Read all the defined content types from the config
        choices = get_configured_cotent_types(self.config)
        parser.add_argument("content_types", nargs="*", choices=choices, help=help)

    def handle(self, *args, **options):

        test_mode = False
        if options["test_mode"]:
            test_mode = True
        for feature in self.config["features"]:
            if feature["content_type"] in options["content_types"]:
                try:
                    import_wfs_feature(feature, test_mode)
                except Exception as e:
                    logger.warning(f"Skipping content_type {feature} : {e}")
