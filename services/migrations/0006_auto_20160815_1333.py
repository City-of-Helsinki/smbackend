# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def invalidate_connection_hashes(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Unit = apps.get_model("services", "Unit")
    for unit in Unit.objects.all():
        unit.connection_hash = None
        unit.save()

class Migration(migrations.Migration):

    dependencies = [
        ('services', '0005_auto_20150828_1348'),
    ]

    operations = [
        migrations.RunPython(invalidate_connection_hashes, invalidate_connection_hashes)
    ]
