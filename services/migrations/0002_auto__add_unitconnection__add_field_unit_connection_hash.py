# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UnitConnection'
        db.create_table('services_unitconnection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='connections', to=orm['services.Unit'])),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('name_fi', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True, null=True)),
            ('name_sv', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True, null=True)),
            ('name_en', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True, null=True)),
            ('www_url', self.gf('django.db.models.fields.URLField')(max_length=400, null=True)),
            ('www_url_fi', self.gf('django.db.models.fields.URLField')(max_length=400, blank=True, null=True)),
            ('www_url_sv', self.gf('django.db.models.fields.URLField')(max_length=400, blank=True, null=True)),
            ('www_url_en', self.gf('django.db.models.fields.URLField')(max_length=400, blank=True, null=True)),
            ('section', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('contact_person', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('phone_mobile', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
        ))
        db.send_create_signal('services', ['UnitConnection'])

        # Adding field 'Unit.connection_hash'
        db.add_column('services_unit', 'connection_hash',
                      self.gf('django.db.models.fields.CharField')(max_length=40, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'UnitConnection'
        db.delete_table('services_unitconnection')

        # Deleting field 'Unit.connection_hash'
        db.delete_column('services_unit', 'connection_hash')


    models = {
        'munigeo.administrativedivision': {
            'Meta': {'unique_together': "(('origin_id', 'type', 'parent'),)", 'object_name': 'AdministrativeDivision'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'ocd_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['munigeo.AdministrativeDivision']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.AdministrativeDivisionType']"})
        },
        'munigeo.administrativedivisiontype': {
            'Meta': {'object_name': 'AdministrativeDivisionType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        'munigeo.municipality': {
            'Meta': {'object_name': 'Municipality'},
            'division': ('django.db.models.fields.related.ForeignKey', [], {'unique': 'True', 'related_name': "'muni'", 'null': 'True', 'to': "orm['munigeo.AdministrativeDivision']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True', 'db_index': 'True'})
        },
        'services.department': {
            'Meta': {'object_name': 'Department'},
            'abbr': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'primary_key': 'True', 'max_length': '20'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"})
        },
        'services.keyword': {
            'Meta': {'unique_together': "(('language', 'name'),)", 'object_name': 'Keyword'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'services.organization': {
            'Meta': {'object_name': 'Organization'},
            'data_source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'max_length': '20'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'})
        },
        'services.service': {
            'Meta': {'object_name': 'Service'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': "orm['services.Service']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'services.unit': {
            'Meta': {'object_name': 'Unit'},
            'address_postal_full': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'address_zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'connection_hash': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True'}),
            'data_source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'department': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['services.Department']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'description_fi': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'description_sv': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'divisions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['munigeo.AdministrativeDivision']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['services.Keyword']"}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3067', 'null': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True', 'db_index': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"}),
            'origin_last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'picture_caption': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'picture_caption_en': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True'}),
            'picture_caption_fi': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True'}),
            'picture_caption_sv': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True', 'null': 'True'}),
            'picture_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'provider_type': ('django.db.models.fields.IntegerField', [], {}),
            'services': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['services.Service']"}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'street_address_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True'}),
            'street_address_fi': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True'}),
            'street_address_sv': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True'}),
            'www_url': ('django.db.models.fields.URLField', [], {'max_length': '400', 'null': 'True'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'})
        },
        'services.unitconnection': {
            'Meta': {'object_name': 'UnitConnection'},
            'contact_person': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'phone_mobile': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'section': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'connections'", 'to': "orm['services.Unit']"}),
            'www_url': ('django.db.models.fields.URLField', [], {'max_length': '400', 'null': 'True'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'max_length': '400', 'blank': 'True', 'null': 'True'})
        }
    }

    complete_apps = ['services']