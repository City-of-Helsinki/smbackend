# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0013_remove_old_values'),
    ]

    operations = [
        migrations.RenameField('Observation', 'new_value', 'value')
    ]
