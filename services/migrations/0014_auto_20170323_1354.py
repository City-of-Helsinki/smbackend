# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0013_unitconnection_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceLeaf',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('name_fi', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_sv', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_en', models.CharField(max_length=200, null=True, db_index=True)),
                ('unit_count', models.PositiveIntegerField(null=True)),
                ('last_modified_time', models.DateTimeField(help_text='Time of last modification', db_index=True)),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceNode',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('name_fi', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_sv', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_en', models.CharField(max_length=200, null=True, db_index=True)),
                ('unit_count', models.PositiveIntegerField(null=True)),
                ('last_modified_time', models.DateTimeField(help_text='Time of last modification', db_index=True)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
                ('leaves', models.ManyToManyField(to='services.ServiceLeaf')),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', null=True, to='services.ServiceNode')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='unitconnection',
            options={'ordering': ['order']},
        ),
    ]
