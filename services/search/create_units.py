import os, sys, django

sys.path.append("/home/juuso/repos/turku/smbackend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smbackend.settings")
django.setup()
import requests
import random
from datetime import datetime
from django.conf import settings
from services.models import (
    Service,
    ServiceNode,
    Unit,
    UnitServiceDetails,
)
from smbackend_turku.importers.utils import (
    set_field,
    set_tku_translated_field,
    UTC_TIMEZONE,
)
from services.management.commands.services_import.services import (
    update_service_node_counts,
)


def create_language_dict(value, target_langs=["fi", "sv", "en"]):
    """
    Helper function that generates a dict with elements for every language with
    the value given as parameter.
    :param value: the value to be set for all the languages
    :return: the dict
    """
    lang_dict = {}
    languages = [language[0] for language in settings.LANGUAGES]
    for lang in languages:
        if lang in target_langs:
            lang_dict[lang] = value
        else:
            lang_dict[lang] = ""

    return lang_dict


def create_units(num_units, id_offs=50000):
    word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    response = requests.get(word_site)
    WORDS = response.content.decode().splitlines()
    for i in range(num_units):

        name = ""
        description = ""
        for n in range(random.randint(1, 4)):
            name += WORDS[random.randint(0, len(WORDS) - 1)] + " "
        for n in range(random.randint(2, 10)):
            description += WORDS[random.randint(0, len(WORDS) - 1)] + " "
        service_id = random.randint(3, 40)
        obj = Unit(id=id_offs + i)
        obj.last_modified_time = datetime.now(UTC_TIMEZONE)

        set_tku_translated_field(
            obj, "name", create_language_dict(name, target_langs=["en"])
        )
        set_tku_translated_field(
            obj, "description", create_language_dict(description, target_langs=["en"])
        )

        obj.save()
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            print("Service not found")
            continue
        UnitServiceDetails.objects.get_or_create(unit=obj, service=service)
        service_nodes = ServiceNode.objects.filter(related_services=service)

        obj.service_nodes.add(*service_nodes)
        obj.save()
    update_service_node_counts


if __name__ == "__main__":
    create_units(30000, id_offs=900000)
