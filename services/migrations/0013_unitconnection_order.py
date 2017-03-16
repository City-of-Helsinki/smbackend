# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0012_unit_data_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='unitconnection',
            name='order',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
