# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0004_auto_20170403_1113'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unitconnection',
            old_name='www_url',
            new_name='www',
        ),
        migrations.RenameField(
            model_name='unitconnection',
            old_name='www_url_en',
            new_name='www_en',
        ),
        migrations.RenameField(
            model_name='unitconnection',
            old_name='www_url_fi',
            new_name='www_fi',
        ),
        migrations.RenameField(
            model_name='unitconnection',
            old_name='www_url_sv',
            new_name='www_sv',
        ),
    ]
