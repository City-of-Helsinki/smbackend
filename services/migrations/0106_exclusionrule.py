# Generated by Django 4.1.7 on 2023-02-17 13:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0105_alter_unit_displayed_service_owner"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExclusionRule",
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
                ("word", models.CharField(max_length=100, verbose_name="Word")),
                (
                    "exclusion",
                    models.CharField(max_length=100, verbose_name="Exclusion"),
                ),
            ],
            options={
                "verbose_name": "Exclusion rule",
                "verbose_name_plural": "Exclusion rules",
                "ordering": ["-id"],
            },
        ),
    ]
