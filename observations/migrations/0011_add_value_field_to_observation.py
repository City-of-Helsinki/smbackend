# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0010_ensure_backwards_non_null_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='new_value',
            field=models.ForeignKey(related_name='instances', to='observations.AllowedValue', null=True),
        ),
        migrations.AlterField(
            model_name='allowedvalue',
            name='identifier',
            field=models.CharField(max_length=50, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='allowedvalue',
            name='name',
            field=models.CharField(max_length=100, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='allowedvalue',
            name='quality',
            field=models.CharField(max_length=50, db_index=True, default='unknown', null=True),
        ),
    ]
