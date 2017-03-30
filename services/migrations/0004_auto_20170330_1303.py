# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0003_auto_20170330_1246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='uuid',
            field=models.UUIDField(editable=False, unique=True, db_index=True),
        ),
    ]
