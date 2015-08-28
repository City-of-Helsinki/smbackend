# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0004_auto_20150629_1354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='phone',
            field=models.CharField(null=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_url',
            field=models.URLField(null=True, max_length=250),
        ),
    ]
