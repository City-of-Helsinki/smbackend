# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-01-06 15:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0071_add_serviceunitcount"),
    ]

    operations = [
        migrations.AlterField(
            model_name="department",
            name="oid",
            field=models.CharField(max_length=30, null=True),
        ),
    ]
