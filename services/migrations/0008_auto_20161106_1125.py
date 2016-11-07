# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0007_auto_20160815_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='services',
            field=models.ManyToManyField(related_name='units', to='services.Service'),
        ),
    ]
