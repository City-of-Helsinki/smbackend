# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def change_quality(apps, schema_editor):
    AllowedValue = apps.get_model('observations', 'AllowedValue')
    a = AllowedValue.objects.get(identifier='plowed', property_id='ice_skating_field_condition')
    a.quality = 'good'
    a.save()

def revert_quality(apps, schema_editor):
    AllowedValue = apps.get_model('observations', 'AllowedValue')
    a = AllowedValue.objects.get(identifier='plowed', property_id='ice_skating_field_condition')
    a.quality = 'satisfactory'
    a.save()

class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0006_swedish_translations'),
    ]

    operations = [
        migrations.RunPython(change_quality, revert_quality)
    ]
