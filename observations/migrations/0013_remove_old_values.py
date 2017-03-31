# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0012_transfer_value_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='categoricalobservation',
            name='value',
        ),
        migrations.RemoveField(
            model_name='continuousobservation',
            name='value',
        ),
        migrations.RemoveField(
            model_name='descriptiveobservation',
            name='value',
        ),
        migrations.RemoveField(
            model_name='descriptiveobservation',
            name='value_en',
        ),
        migrations.RemoveField(
            model_name='descriptiveobservation',
            name='value_fi',
        ),
        migrations.RemoveField(
            model_name='descriptiveobservation',
            name='value_sv',
        ),
    ]
