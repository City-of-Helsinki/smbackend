# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0007_data_migrate_skating_quality'),
    ]

    operations = [
        migrations.AddField(
            model_name='descriptiveobservation',
            name='value_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='descriptiveobservation',
            name='value_fi',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='descriptiveobservation',
            name='value_sv',
            field=models.TextField(null=True),
        ),
    ]
