import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0088_create_search_view"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="service_names_en",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="unit",
            name="service_names_fi",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="unit",
            name="service_names_sv",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=200), default=list, size=None
            ),
        ),
    ]
