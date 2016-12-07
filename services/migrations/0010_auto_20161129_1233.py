# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0009_unitgeometry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unitgeometry',
            name='unit',
        ),
        migrations.AddField(
            model_name='unit',
            name='geometry',
            field=django.contrib.gis.db.models.fields.GeometryField(null=True, srid=3067),
        ),
        migrations.DeleteModel(
            name='UnitGeometry',
        ),
    ]
