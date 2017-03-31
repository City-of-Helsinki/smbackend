# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def copy_values(apps, schema_editor):
    CategoricalObservation = apps.get_model('observations', 'CategoricalObservation')
    for co in CategoricalObservation.objects.all():
        co.new_value = co.value
        co.save()

def copy_values_back(apps, schema_editor):
    CategoricalObservation = apps.get_model('observations', 'CategoricalObservation')
    for co in CategoricalObservation.objects.all():
        co.value = co.new_value
        co.save()

class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0011_add_value_field_to_observation'),
    ]

    operations = [
        migrations.RunPython(copy_values, copy_values_back),
    ]
