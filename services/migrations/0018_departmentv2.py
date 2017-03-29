# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0017_auto_20170327_1520'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentV2',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('business_id', models.CharField(max_length=10)),
                ('hierarchy_level', models.SmallIntegerField()),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('object_identifier', models.CharField(max_length=20)),
            ],
        ),
    ]
