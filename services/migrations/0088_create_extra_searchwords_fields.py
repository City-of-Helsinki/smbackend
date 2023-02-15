import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0087_create_service_names_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="extra_searchwords_en",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="unit",
            name="extra_searchwords_fi",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="unit",
            name="extra_searchwords_sv",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200), default=list, size=None
            ),
        ),
    ]
