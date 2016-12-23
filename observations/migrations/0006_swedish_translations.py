# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def add_swedish_translations(apps, schema_editor):
    AllowedValue = apps.get_model('observations', 'AllowedValue')
    for v in AllowedValue.objects.all():
        if v.name_fi == 'Aurattu':
            v.name_sv = 'Plogad'
            v.name_en = 'Cleared of snow'
        elif v.name_fi == 'Jäädytetty':
            v.name_sv = 'Isad'
            v.name_en = 'Ice-covered'
        elif v.name_fi == 'Jäädytys aloitettu':
            v.name_sv = 'Isningen har inletts'
            v.name_en = 'The icing has begun'
        elif v.name_fi == 'Suljettu':
            v.name_sv = 'Stängd'
        elif v.name_fi == 'Hyvä':
            v.name_sv = 'Bra'
        elif v.name_fi == 'Tyydyttävä':
            v.name_sv = 'Hyfsad'
            v.name_en = 'Decent'
        elif v.name_fi == 'Heikko':
            v.name_sv = 'Svag'
        elif v.name_fi == 'Lumenpuute':
            v.name_sv = 'Snöbrist'
            v.name_en = 'Lack of snow'
        elif v.name_fi == 'Kilpailut/harjoitukset':
            v.name_sv = 'Tävlingar/träningar'
        elif v.name_fi == 'Roskainen':
            v.name_sv = 'Skräpig'
        elif v.name_fi == 'Latu pohjattu (ei latu-uraa)':
            v.name_sv = 'Grunden lagd (inget skidspår)'
            v.name_en = 'Foundation laid (no skiing trail)'
        elif v.name_fi == 'Lumetus kesken':
            v.name_sv = 'Snöproduktionen oavslutad'
            v.name_en = 'Snowmaking unfinished'
        elif v.name_fi == 'Kunnostettu':
            v.name_sv = 'Iståndsatt'
        v.save()

def do_nothing(*args):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0005_auto_20161205_0813'),
    ]

    operations = [
        migrations.RunPython(add_swedish_translations, do_nothing),
    ]
