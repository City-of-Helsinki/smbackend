# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-02 13:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0031_translate_unit_postal_address"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="unit",
            name="address_city",
        ),
    ]
