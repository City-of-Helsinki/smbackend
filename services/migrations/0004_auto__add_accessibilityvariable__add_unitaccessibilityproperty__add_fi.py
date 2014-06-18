# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AccessibilityVariable'
        db.create_table('services_accessibilityvariable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('services', ['AccessibilityVariable'])

        # Adding model 'UnitAccessibilityProperty'
        db.create_table('services_unitaccessibilityproperty', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['services.Unit'], related_name='accessibility_properties')),
            ('variable', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['services.AccessibilityVariable'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('services', ['UnitAccessibilityProperty'])

        # Adding field 'Unit.accessibility_property_hash'
        db.add_column('services_unit', 'accessibility_property_hash',
                      self.gf('django.db.models.fields.CharField')(max_length=40, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'AccessibilityVariable'
        db.delete_table('services_accessibilityvariable')

        # Deleting model 'UnitAccessibilityProperty'
        db.delete_table('services_unitaccessibilityproperty')

        # Deleting field 'Unit.accessibility_property_hash'
        db.delete_column('services_unit', 'accessibility_property_hash')


    models = {
        'munigeo.administrativedivision': {
            'Meta': {'unique_together': "(('origin_id', 'type', 'parent'),)", 'object_name': 'AdministrativeDivision'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.Municipality']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '100', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '100', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '100', 'null': 'True'}),
            'ocd_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'unique': 'True', 'null': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'to': "orm['munigeo.AdministrativeDivision']", 'related_name': "'children'", 'null': 'True'}),
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
            'division': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.AdministrativeDivision']", 'related_name': "'muni'", 'unique': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '100', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '100', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '100', 'null': 'True'})
        },
        'services.accessibilityvariable': {
            'Meta': {'object_name': 'AccessibilityVariable'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'services.department': {
            'Meta': {'object_name': 'Department'},
            'abbr': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20'}),
            'id': ('django.db.models.fields.CharField', [], {'primary_key': 'True', 'max_length': '20'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"})
        },
        'services.keyword': {
            'Meta': {'unique_together': "(('language', 'name'),)", 'object_name': 'Keyword'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100'})
        },
        'services.organization': {
            'Meta': {'object_name': 'Organization'},
            'data_source_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'max_length': '20'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'})
        },
        'services.service': {
            'Meta': {'object_name': 'Service'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'identical_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Service']", 'related_name': "'duplicates'", 'null': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'to': "orm['services.Service']", 'related_name': "'children'", 'null': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'services.unit': {
            'Meta': {'object_name': 'Unit'},
            'accessibility_property_hash': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True'}),
            'address_postal_full': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'address_zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'connection_hash': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True'}),
            'data_source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'department': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Department']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'description_fi': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'description_sv': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'divisions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['munigeo.AdministrativeDivision']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['services.Keyword']"}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3067', 'null': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.Municipality']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'db_index': 'True', 'max_length': '200', 'null': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"}),
            'origin_last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True'}),
            'picture_caption': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'picture_caption_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'}),
            'picture_caption_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'}),
            'picture_caption_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'}),
            'picture_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'provider_type': ('django.db.models.fields.IntegerField', [], {}),
            'services': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['services.Service']"}),
            'street_address': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'street_address_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100', 'null': 'True'}),
            'street_address_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100', 'null': 'True'}),
            'street_address_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100', 'null': 'True'}),
            'www_url': ('django.db.models.fields.URLField', [], {'max_length': '400', 'null': 'True'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'})
        },
        'services.unitaccessibilityproperty': {
            'Meta': {'object_name': 'UnitAccessibilityProperty'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Unit']", 'related_name': "'accessibility_properties'"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'variable': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.AccessibilityVariable']"})
        },
        'services.unitconnection': {
            'Meta': {'object_name': 'UnitConnection'},
            'contact_person': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'phone_mobile': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'section': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Unit']", 'related_name': "'connections'"}),
            'www_url': ('django.db.models.fields.URLField', [], {'max_length': '400', 'null': 'True'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '400', 'null': 'True'})
        }
    }

    complete_apps = ['services']