# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0002_auto_20161107_0220'),
    ]

    operations = [
        migrations.AddField(
            model_name='allowedvalue',
            name='quality',
            field=models.CharField(max_length=50, db_index=True, default='unknown'),
        ),
    ]
