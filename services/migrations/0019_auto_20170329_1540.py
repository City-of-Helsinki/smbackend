# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0018_departmentv2'),
    ]

    operations = [
        migrations.AddField(
            model_name='departmentv2',
            name='name_en',
            field=models.CharField(max_length=200, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='departmentv2',
            name='name_fi',
            field=models.CharField(max_length=200, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='departmentv2',
            name='name_sv',
            field=models.CharField(max_length=200, db_index=True, null=True),
        ),
    ]
