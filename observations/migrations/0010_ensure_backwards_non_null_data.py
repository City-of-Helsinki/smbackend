# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def nop(apps, schema_editor):
    pass

def delete_null_values(apps, schema_editor):
    CategoricalObservation = apps.get_model('observations', 'CategoricalObservation')
    CategoricalObservation.objects.filter(value__isnull=True).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0009_allow_null_observation_values'),
    ]

    operations = [
        migrations.RunPython(nop, delete_null_values),
    ]
