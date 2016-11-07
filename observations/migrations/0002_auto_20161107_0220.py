# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observation',
            name='unit',
            field=models.ForeignKey(related_name='observations', to='services.Unit', help_text='The unit the observation is about'),
        ),
    ]
