# Generated by Django 4.1.3 on 2023-01-04 06:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0104_unit_new_contract_type_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="unit",
            name="displayed_service_owner",
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name="unit",
            name="displayed_service_owner_en",
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name="unit",
            name="displayed_service_owner_fi",
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name="unit",
            name="displayed_service_owner_sv",
            field=models.CharField(max_length=120, null=True),
        ),
    ]