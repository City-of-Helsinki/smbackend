# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoricalobservation',
            name='value',
            field=models.ForeignKey(related_name='instances', to='observations.AllowedValue', db_column='id'),
        ),
    ]
