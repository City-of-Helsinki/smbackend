# Generated by Django 4.1.2 on 2022-11-07 14:54

from django.db import migrations, models

import services.models.statistic


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0101_alter_unitconnection_section_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="RequestStatistic",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timeframe",
                    models.CharField(max_length=10, verbose_name="Timeframe"),
                ),
                (
                    "request_counter",
                    models.IntegerField(default=0, verbose_name="Request counter"),
                ),
                (
                    "details",
                    models.JSONField(
                        default=services.models.statistic.default_details,
                        verbose_name="Details",
                    ),
                ),
            ],
            options={
                "verbose_name": "Request statistic",
                "verbose_name_plural": "Request statistics",
                "ordering": ["-id"],
            },
        ),
    ]
