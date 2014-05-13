# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Keyword'
        db.create_table('services_keyword', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=100)),
        ))
        db.send_create_signal('services', ['Keyword'])

        # Adding unique constraint on 'Keyword', fields ['language', 'name']
        db.create_unique('services_keyword', ['language', 'name'])

        # Adding model 'Service'
        db.create_table('services_service', (
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=200)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_en', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(null=True, related_name='children', to=orm['services.Service'])),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('services', ['Service'])

        # Adding model 'Organization'
        db.create_table('services_organization', (
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True, max_length=20)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=200)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_en', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('data_source_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
        ))
        db.send_create_signal('services', ['Organization'])

        # Adding model 'Department'
        db.create_table('services_department', (
            ('id', self.gf('django.db.models.fields.CharField')(primary_key=True, max_length=20)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=200)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_en', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('abbr', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=20)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['services.Organization'])),
        ))
        db.send_create_signal('services', ['Department'])

        # Adding model 'Unit'
        db.create_table('services_unit', (
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('data_source_url', self.gf('django.db.models.fields.URLField')(null=True, max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=200)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('name_en', self.gf('django.db.models.fields.CharField')(db_index=True, null=True, blank=True, max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('description_fi', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description_sv', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('provider_type', self.gf('django.db.models.fields.IntegerField')()),
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=3067, null=True)),
            ('department', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['services.Department'])),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['services.Organization'])),
            ('street_address', self.gf('django.db.models.fields.CharField')(null=True, max_length=100)),
            ('street_address_fi', self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=100)),
            ('street_address_sv', self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=100)),
            ('street_address_en', self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=100)),
            ('address_zip', self.gf('django.db.models.fields.CharField')(null=True, max_length=10)),
            ('phone', self.gf('django.db.models.fields.CharField')(null=True, max_length=30)),
            ('email', self.gf('django.db.models.fields.EmailField')(null=True, max_length=50)),
            ('www_url', self.gf('django.db.models.fields.URLField')(null=True, max_length=400)),
            ('www_url_fi', self.gf('django.db.models.fields.URLField')(null=True, blank=True, max_length=400)),
            ('www_url_sv', self.gf('django.db.models.fields.URLField')(null=True, blank=True, max_length=400)),
            ('www_url_en', self.gf('django.db.models.fields.URLField')(null=True, blank=True, max_length=400)),
            ('address_postal_full', self.gf('django.db.models.fields.CharField')(null=True, max_length=100)),
            ('municipality', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['munigeo.Municipality'])),
            ('picture_url', self.gf('django.db.models.fields.URLField')(null=True, max_length=200)),
            ('picture_caption', self.gf('django.db.models.fields.CharField')(null=True, max_length=200)),
            ('picture_caption_fi', self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=200)),
            ('picture_caption_sv', self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=200)),
            ('picture_caption_en', self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=200)),
            ('origin_last_modified_time', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal('services', ['Unit'])

        # Adding M2M table for field services on 'Unit'
        m2m_table_name = db.shorten_name('services_unit_services')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('unit', models.ForeignKey(orm['services.unit'], null=False)),
            ('service', models.ForeignKey(orm['services.service'], null=False))
        ))
        db.create_unique(m2m_table_name, ['unit_id', 'service_id'])

        # Adding M2M table for field divisions on 'Unit'
        m2m_table_name = db.shorten_name('services_unit_divisions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('unit', models.ForeignKey(orm['services.unit'], null=False)),
            ('administrativedivision', models.ForeignKey(orm['munigeo.administrativedivision'], null=False))
        ))
        db.create_unique(m2m_table_name, ['unit_id', 'administrativedivision_id'])

        # Adding M2M table for field keywords on 'Unit'
        m2m_table_name = db.shorten_name('services_unit_keywords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('unit', models.ForeignKey(orm['services.unit'], null=False)),
            ('keyword', models.ForeignKey(orm['services.keyword'], null=False))
        ))
        db.create_unique(m2m_table_name, ['unit_id', 'keyword_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Keyword', fields ['language', 'name']
        db.delete_unique('services_keyword', ['language', 'name'])

        # Deleting model 'Keyword'
        db.delete_table('services_keyword')

        # Deleting model 'Service'
        db.delete_table('services_service')

        # Deleting model 'Organization'
        db.delete_table('services_organization')

        # Deleting model 'Department'
        db.delete_table('services_department')

        # Deleting model 'Unit'
        db.delete_table('services_unit')

        # Removing M2M table for field services on 'Unit'
        db.delete_table(db.shorten_name('services_unit_services'))

        # Removing M2M table for field divisions on 'Unit'
        db.delete_table(db.shorten_name('services_unit_divisions'))

        # Removing M2M table for field keywords on 'Unit'
        db.delete_table(db.shorten_name('services_unit_keywords'))


    models = {
        'munigeo.administrativedivision': {
            'Meta': {'object_name': 'AdministrativeDivision', 'unique_together': "(('origin_id', 'type', 'parent'),)"},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'ocd_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'unique': 'True', 'max_length': '200'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'null': 'True', 'related_name': "'children'", 'to': "orm['munigeo.AdministrativeDivision']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.AdministrativeDivisionType']"})
        },
        'munigeo.administrativedivisiontype': {
            'Meta': {'object_name': 'AdministrativeDivisionType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '30'})
        },
        'munigeo.municipality': {
            'Meta': {'object_name': 'Municipality'},
            'division': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'muni'", 'unique': 'True', 'to': "orm['munigeo.AdministrativeDivision']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '100'})
        },
        'services.department': {
            'Meta': {'object_name': 'Department'},
            'abbr': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20'}),
            'id': ('django.db.models.fields.CharField', [], {'primary_key': 'True', 'max_length': '20'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"})
        },
        'services.keyword': {
            'Meta': {'object_name': 'Keyword', 'unique_together': "(('language', 'name'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100'})
        },
        'services.organization': {
            'Meta': {'object_name': 'Organization'},
            'data_source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'max_length': '20'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'})
        },
        'services.service': {
            'Meta': {'object_name': 'Service'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'null': 'True', 'related_name': "'children'", 'to': "orm['services.Service']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'services.unit': {
            'Meta': {'object_name': 'Unit'},
            'address_postal_full': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100'}),
            'address_zip': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '10'}),
            'data_source_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '200'}),
            'department': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['services.Department']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_fi': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_sv': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'divisions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['munigeo.AdministrativeDivision']"}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['services.Keyword']"}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3067', 'null': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"}),
            'origin_last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '30'}),
            'picture_caption': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200'}),
            'picture_caption_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'picture_caption_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'picture_caption_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'picture_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '200'}),
            'provider_type': ('django.db.models.fields.IntegerField', [], {}),
            'services': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['services.Service']"}),
            'street_address': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100'}),
            'street_address_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'street_address_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'street_address_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'www_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'null': 'True', 'blank': 'True', 'max_length': '400'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'null': 'True', 'blank': 'True', 'max_length': '400'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'null': 'True', 'blank': 'True', 'max_length': '400'})
        }
    }

    complete_apps = ['services']