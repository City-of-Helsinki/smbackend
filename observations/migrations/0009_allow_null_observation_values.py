# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0008_translate_descriptive_observations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoricalobservation',
            name='value',
            field=models.ForeignKey(to='observations.AllowedValue', db_column='id', related_name='instances', null=True),
        ),
    ]
