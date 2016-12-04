# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0012_unit_data_source'),
        ('observations', '0002_auto_20161115_1236'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitLatestObservation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AlterField(
            model_name='observation',
            name='unit',
            field=models.ForeignKey(help_text='The unit the observation is about', related_name='observation_history', to='services.Unit'),
        ),
        migrations.AddField(
            model_name='unitlatestobservation',
            name='observation',
            field=models.ForeignKey(to='observations.Observation'),
        ),
        migrations.AddField(
            model_name='unitlatestobservation',
            name='property',
            field=models.ForeignKey(to='observations.ObservableProperty'),
        ),
        migrations.AddField(
            model_name='unitlatestobservation',
            name='unit',
            field=models.ForeignKey(to='services.Unit', related_name='latest_observations'),
        ),
        migrations.AlterUniqueTogether(
            name='unitlatestobservation',
            unique_together=set([('unit', 'property', 'observation')]),
        ),
    ]
