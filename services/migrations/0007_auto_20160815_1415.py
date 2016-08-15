# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0006_auto_20160815_1333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unitconnection',
            name='contact_person',
            field=models.CharField(null=True, max_length=80),
        ),
    ]
