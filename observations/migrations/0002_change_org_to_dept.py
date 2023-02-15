# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-05 11:40
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("observations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userorganization",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="services.Department"
            ),
        ),
    ]
