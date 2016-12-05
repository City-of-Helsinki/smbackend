# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('services', '0012_unit_data_source'),
        ('observations', '0004_auto_20161203_2322'),
    ]

    operations = [
        migrations.CreateModel(
            name='PluralityAuthToken',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('key', models.CharField(max_length=40, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='auth_tokens')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserOrganization',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('organization', models.ForeignKey(to='services.Organization')),
                ('user', models.OneToOneField(related_name='organization', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='observation',
            name='units',
            field=models.ManyToManyField(to='services.Unit', through='observations.UnitLatestObservation'),
        ),
        migrations.AddField(
            model_name='observation',
            name='auth',
            field=models.ForeignKey(to='observations.PluralityAuthToken', null=True),
        ),
    ]
