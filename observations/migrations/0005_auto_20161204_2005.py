# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0012_unit_data_source'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('observations', '0004_auto_20161203_2322'),
    ]

    operations = [
        migrations.CreateModel(
            name='PluralityAuthToken',
            fields=[
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='auth_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='observation',
            name='units',
            field=models.ManyToManyField(to='services.Unit', through='observations.UnitLatestObservation'),
        ),
    ]
