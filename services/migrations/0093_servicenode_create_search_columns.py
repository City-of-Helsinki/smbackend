# Generated by Django 4.0.2 on 2022-03-11 07:46

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0092_trigram_index_service_and_unit_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicenode",
            name="search_column_en",
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddField(
            model_name="servicenode",
            name="search_column_fi",
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddField(
            model_name="servicenode",
            name="search_column_sv",
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name="servicenode",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_column_fi"], name="services_se_search__b46246_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="servicenode",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_column_sv"], name="services_se_search__f492a0_gin"
            ),
        ),
        migrations.AddIndex(
            model_name="servicenode",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_column_en"], name="services_se_search__efc749_gin"
            ),
        ),
    ]
