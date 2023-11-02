# -*- coding: utf-8 -*-
import logging
import re
import sys

import pytz
import requests
from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import activate, get_language

from services.management.commands.services_import.aliases import import_aliases
from services.management.commands.services_import.departments import import_departments
from services.management.commands.services_import.entrances import import_entrances
from services.management.commands.services_import.properties import (
    import_unit_properties,
)
from services.management.commands.services_import.services import (
    import_services,
    remove_empty_service_nodes,
    update_mobility_service_node_counts,
    update_mobility_service_nodes,
    update_service_counts,
    update_service_node_counts,
    update_service_organization_counts,
    update_service_root_service_nodes,
)
from services.management.commands.services_import.units import import_units

URL_BASE = "https://www.hel.fi/palvelukarttaws/rest/v4/"
GK25_SRID = 3879

UTC_TIMEZONE = pytz.timezone("UTC")


class Command(BaseCommand):
    help = "Import services from TPR Palvelukartta REST API"
    importer_types = [
        "departments",
        "services",
        "units",
        "aliases",
        "entrances",
        "unit_properties",
    ]
    supported_languages = [lang[0] for lang in settings.LANGUAGES]

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            method = "import_%s" % imp
            assert getattr(self, method, False), "No importer defined for %s" % method

        self.services = {}
        self.existing_service_ids = None
        self.existing_service_node_ids = None

    def add_arguments(self, parser):
        parser.add_argument("import_types", nargs="*", choices=self.importer_types)
        parser.add_argument(
            "--cached",
            action="store_true",
            dest="cached",
            default=False,
            help="cache HTTP requests",
        )
        parser.add_argument(
            "--single",
            action="store",
            dest="id",
            default=None,
            help="import only single entity",
        )

    def clean_text(self, text):
        # text = text.replace('\n', ' ')
        # text = text.replace(u'\u00a0', ' ')
        # remove consecutive whitespaces
        text = re.sub(r"\s\s+", " ", text, re.U)
        # remove nil bytes
        text = text.replace("\u0000", " ")
        text = text.strip()
        return text

    def pk_get(self, resource_name, res_id=None, v3=False):
        url = "%s%s/" % (URL_BASE, resource_name)
        if res_id is None:
            url = "%s%s/" % (url, res_id)
        if v3:
            url = url.replace("v4", "v3")
        resp = requests.get(url, timeout=120)
        assert resp.status_code == 200, "fuu status code {}".format(resp.status_code)
        return resp.json()

    def _save_translated_field(
        self, obj, obj_field_name, info, info_field_name, max_length=None
    ):
        for lang in ("fi", "sv", "en"):
            key = "%s_%s" % (info_field_name, lang)
            if key in info:
                val = self.clean_text(info[key])
            else:
                val = None
            if max_length and val and len(val) > max_length:
                if self.verbosity:
                    self.logger.warning(
                        "%s: field '%s' too long" % (obj, obj_field_name)
                    )
                val = None
            obj_key = "%s_%s" % (obj_field_name, lang)
            obj_val = getattr(obj, obj_key, None)
            if obj_val == val:
                continue

            setattr(obj, obj_key, val)
            if lang == "fi":
                setattr(obj, obj_field_name, val)
            obj._changed = True

    def _set_field(self, obj, field_name, val):
        if not hasattr(obj, field_name):
            print(vars(obj))
        obj_val = getattr(obj, field_name)
        if obj_val == val:
            return
        setattr(obj, field_name, val)
        obj._changed = True

    @db.transaction.atomic
    def import_departments(self, noop=False):
        import_departments(logger=self.logger, noop=noop)

    def import_aliases(self):
        import_aliases()

    def import_entrances(self):
        import_entrances()

    def import_unit_properties(self):
        import_unit_properties()

    def _fetch_unit_accessibility_properties(self, unit_pk):
        if self.verbosity:
            self.logger.info(
                "Fetching unit accessibility " "properties for unit {}".format(unit_pk)
            )
        obj_list = self.pk_get("unit/{}/accessibility".format(unit_pk))
        return obj_list

    def import_units(self, pk=None):
        if pk is not None:
            import_units(fetch_only_id=pk)
            return
        import_units()
        update_service_node_counts()
        remove_empty_service_nodes(self.logger)
        update_service_counts()
        update_service_organization_counts()
        update_mobility_service_nodes()
        update_mobility_service_node_counts()

    @db.transaction.atomic
    def import_services(self):
        import_services(logger=self.logger, noop=False, importer=self)
        update_service_root_service_nodes()

    def handle(self, **options):
        self.options = options
        self.verbosity = int(options.get("verbosity", 1))
        self.dept_syncher = None
        self.logger = logging.getLogger(__name__)
        self.services_changed = False

        # if options['cached']:
        #     requests_cache.install_cache('services_import')

        # Activate the default language for the duration of the import
        # to make sure translated fields are populated correctly.
        old_lang = get_language()
        activate(settings.LANGUAGES[0][0])

        import_count = 0
        for imp in self.importer_types:
            if imp not in self.options["import_types"]:
                continue
            method = getattr(self, "import_%s" % imp)
            if self.verbosity:
                print("Importing %s..." % imp)
            if "id" in options and options.get("id"):
                method(pk=options["id"])
            else:
                method()
            import_count += 1

        # if self.services_changed:
        #     self.update_root_services()

        if not import_count:
            sys.stderr.write("Nothing to import.\n")
        activate(old_lang)
