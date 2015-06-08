# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_auto_20150511_1945'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitAlias',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('second', models.IntegerField(unique=True, db_index=True)),
                ('first', models.ForeignKey(to='services.Unit', related_name='aliases')),
            ],
        ),
    ]
