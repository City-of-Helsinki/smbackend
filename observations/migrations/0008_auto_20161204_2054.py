# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('services', '0012_unit_data_source'),
        ('observations', '0007_auto_20161204_2023'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserOrganization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('organization', models.ForeignKey(to='services.Organization')),
                ('user', models.OneToOneField(related_name='organization', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterModelOptions(
            name='observation',
            options={'ordering': ['-time']},
        ),
    ]
