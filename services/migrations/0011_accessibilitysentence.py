# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0010_auto_20170406_0110'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessibilitySentence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('group_name', models.CharField(max_length=100)),
                ('group', models.CharField(max_length=100)),
                ('group_fi', models.CharField(max_length=100, null=True)),
                ('group_sv', models.CharField(max_length=100, null=True)),
                ('group_en', models.CharField(max_length=100, null=True)),
                ('sentence', models.TextField()),
                ('sentence_fi', models.TextField(null=True)),
                ('sentence_sv', models.TextField(null=True)),
                ('sentence_en', models.TextField(null=True)),
                ('unit', models.ForeignKey(to='services.Unit')),
            ],
        ),
    ]
