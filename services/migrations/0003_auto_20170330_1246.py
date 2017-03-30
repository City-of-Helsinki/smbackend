# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_auto_20170330_1237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='department',
            name='organization_type',
            field=models.CharField(null=True, max_length=50),
        ),
    ]
