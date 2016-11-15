# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0008_auto_20161106_1125'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitGeometry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('path', django.contrib.gis.db.models.fields.MultiLineStringField(srid=3067)),
                ('unit', models.OneToOneField(to='services.Unit', related_name='geometry')),
            ],
        ),
    ]
