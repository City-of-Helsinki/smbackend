# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0011_unit_extensions'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='data_source',
            field=models.CharField(null=True, max_length=20, default='tprek'),
            preserve_default=False
        ),
    ]
