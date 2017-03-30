# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0004_auto_20170330_1303'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitAlias',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('second', models.IntegerField(db_index=True, unique=True)),
                ('first', models.ForeignKey(related_name='aliases', to='services.Unit')),
            ],
        ),
    ]
