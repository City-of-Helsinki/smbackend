# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0005_auto_20161204_2005'),
    ]

    operations = [
        migrations.AddField(
            model_name='pluralityauthtoken',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
