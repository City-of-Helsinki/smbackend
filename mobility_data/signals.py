from django.core import management
from django.db.models.signals import post_save
from django.dispatch import receiver

from mobility_data.constants import DATA_SOURCE_IMPORTERS
from mobility_data.models import DataSource


@receiver(post_save, sender=DataSource)
def data_source_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    if obj.run_importer:
        importer = DATA_SOURCE_IMPORTERS[obj.type_name]
        if importer["to_services_list"]:
            management.call_command("turku_services_import", importer["importer_name"])
        else:
            management.call_command(f"import_{importer['importer_name']}")
