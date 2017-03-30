# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='abbr',
            field=models.CharField(max_length=50, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='abbr_en',
            field=models.CharField(max_length=50, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='abbr_fi',
            field=models.CharField(max_length=50, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='abbr_sv',
            field=models.CharField(max_length=50, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_city',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_city_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_city_fi',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_city_sv',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_postal_full',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_postal_full_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_postal_full_fi',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_postal_full_sv',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='address_zip',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='organization',
            field=models.ForeignKey(to='services.Organization', null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='organization_type',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='phone',
            field=models.CharField(max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='street_address',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='street_address_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='street_address_fi',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='street_address_sv',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='www',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='www_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='www_fi',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='department',
            name='www_sv',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='department',
            name='object_identifier',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
