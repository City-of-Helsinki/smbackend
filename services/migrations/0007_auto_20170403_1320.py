# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0006_auto_20170403_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='unitconnection',
            name='contact_person',
            field=models.CharField(max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='unitconnection',
            name='phone',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
