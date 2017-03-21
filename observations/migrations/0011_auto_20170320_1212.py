# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0010_ensure_backwards_non_null_data'),
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
        migrations.AddField(
            model_name='observation',
            name='value',
            field=models.ForeignKey(related_name='instances', to='observations.AllowedValue', null=True),
        ),
        migrations.AlterField(
            model_name='allowedvalue',
            name='identifier',
            field=models.CharField(max_length=50, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='allowedvalue',
            name='name',
            field=models.CharField(max_length=100, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='allowedvalue',
            name='quality',
            field=models.CharField(max_length=50, db_index=True, default='unknown', null=True),
        ),
    ]
