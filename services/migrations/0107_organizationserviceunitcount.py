# Generated by Django 4.1.7 on 2023-03-21 05:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0106_exclusionrule"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationServiceUnitCount",
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
                ("count", models.PositiveIntegerField()),
                (
                    "organization",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="services.department",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unit_count_organizations",
                        to="services.service",
                    ),
                ),
            ],
            options={
                "unique_together": {("service", "organization")},
            },
        ),
    ]
