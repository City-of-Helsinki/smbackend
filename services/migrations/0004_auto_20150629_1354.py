# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0003_unitalias'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitIdentifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('namespace', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='unit',
            name='identifier_hash',
            field=models.CharField(help_text='Automatically generated hash of other identifiers', max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='unitidentifier',
            name='unit',
            field=models.ForeignKey(related_name='identifiers', to='services.Unit'),
        ),
    ]
