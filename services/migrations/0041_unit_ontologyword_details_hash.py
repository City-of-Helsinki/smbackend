# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-01-09 14:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0040_unit_ontologyword_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="ontologyword_details_hash",
            field=models.CharField(max_length=40, null=True),
        ),
    ]
