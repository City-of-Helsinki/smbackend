# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-19 12:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0024_remove_unit_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="public",
            field=models.BooleanField(default=True),
        ),
    ]
