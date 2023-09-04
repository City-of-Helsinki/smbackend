# Generated by Django 4.1.7 on 2023-07-14 07:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0110_mobilityservicenode"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="mobility_service_nodes",
            field=models.ManyToManyField(
                related_name="units", to="services.mobilityservicenode"
            ),
        ),
    ]