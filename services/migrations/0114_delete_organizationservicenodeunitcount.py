# Generated by Django 4.2.6 on 2023-10-26 08:08

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0113_mobilityservicenodeunitcount"),
    ]

    operations = [
        migrations.DeleteModel(
            name="OrganizationServiceNodeUnitCount",
        ),
    ]
