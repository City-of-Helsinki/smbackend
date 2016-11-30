# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0010_auto_20161129_1233'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='extensions',
            field=django.contrib.postgres.fields.hstore.HStoreField(null=True),
        ),
    ]
