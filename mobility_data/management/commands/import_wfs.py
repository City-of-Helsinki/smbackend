import logging

import yaml
from django.core.management import BaseCommand

from mobility_data.importers.utils import get_root_dir
from mobility_data.importers.wfs import import_wfs_feature

logger = logging.getLogger("mobility_data")

CONFIG_FILE = f"{get_root_dir()}/mobility_data/importers/data/wfs_importer_config.yml"


def get_yaml_config(file):
    return yaml.safe_load(open(file, "r", encoding="utf-8"))


def get_configured_cotent_type_names(config=None):
    if not config:
        config = get_yaml_config(CONFIG_FILE)
    return [f["content_type_name"] for f in config["features"]]


class Command(BaseCommand):
    config = get_yaml_config(CONFIG_FILE)
    # Read all the defined content types from the config
    choices = get_configured_cotent_type_names(config)

    def add_arguments(self, parser):

        parser.add_argument(
            "--data-file",
            nargs="?",
            help="Input data file.",
        )
        parser.add_argument(
            "--config-file",
            nargs="?",
            help="YAML config file for features.",
        )
        parser.add_argument(
            "content_type_names", nargs="*", help=", ".join(self.choices)
        )

    def handle(self, *args, **options):
        if options["config_file"]:
            self.config = get_yaml_config(options["config_file"])

        data_file = None
        if options["data_file"]:
            data_file = options["data_file"]

        # Check if ContentTypes given as arguments exists.
        if options["content_type_names"]:
            for content_type_name in options["content_type_names"]:
                if content_type_name not in self.choices:
                    logger.warning(
                        f"ContentType {content_type_name} not found in config, discarding..."
                    )

        for feature in self.config["features"]:
            if (
                options["config_file"]
                or feature["content_type_name"] in options["content_type_names"]
            ):
                try:
                    import_wfs_feature(feature, data_file)
                except Exception as e:
                    logger.warning(f"Skipping content_type {feature} : {e}")
