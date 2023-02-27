# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-01-06 15:17
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("observations", "0006_observableproperty_expiration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="observation",
            name="auth",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="observations.PluralityAuthToken",
            ),
        ),
        migrations.AlterField(
            model_name="observation",
            name="property",
            field=models.ForeignKey(
                help_text="The property observed",
                on_delete=django.db.models.deletion.PROTECT,
                to="observations.ObservableProperty",
            ),
        ),
        migrations.AlterField(
            model_name="observation",
            name="unit",
            field=models.ForeignKey(
                help_text="The unit the observation is about",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="observation_history",
                to="services.Unit",
            ),
        ),
        migrations.AlterField(
            model_name="observation",
            name="value",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="instances",
                to="observations.AllowedValue",
            ),
        ),
        migrations.AlterField(
            model_name="pluralityauthtoken",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="auth_tokens",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
