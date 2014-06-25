# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Unit.root_services'
        db.add_column('services_unit', 'root_services',
                      self.gf('django.db.models.fields.CommaSeparatedIntegerField')(null=True, max_length=50),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Unit.root_services'
        db.delete_column('services_unit', 'root_services')


    models = {
        'munigeo.administrativedivision': {
            'Meta': {'unique_together': "(('origin_id', 'type', 'parent'),)", 'object_name': 'AdministrativeDivision'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100', 'db_index': 'True'}),
            'ocd_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'max_length': '200', 'unique': 'True'}),
            'origin_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'null': 'True', 'to': "orm['munigeo.AdministrativeDivision']", 'related_name': "'children'"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'start': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['munigeo.AdministrativeDivisionType']"})
        },
        'munigeo.administrativedivisiontype': {
            'Meta': {'object_name': 'AdministrativeDivisionType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'unique': 'True'})
        },
        'munigeo.municipality': {
            'Meta': {'object_name': 'Municipality'},
            'division': ('django.db.models.fields.related.ForeignKey', [], {'unique': 'True', 'null': 'True', 'to': "orm['munigeo.AdministrativeDivision']", 'related_name': "'muni'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'null': 'True', 'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100', 'db_index': 'True'})
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
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
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
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'})
        },
        'services.service': {
            'Meta': {'object_name': 'Service'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'identical_to': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['services.Service']", 'related_name': "'duplicates'"}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'null': 'True', 'to': "orm['services.Service']", 'related_name': "'children'"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'services.unit': {
            'Meta': {'object_name': 'Unit'},
            'accessibility_property_hash': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '40'}),
            'address_postal_full': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100'}),
            'address_zip': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '10'}),
            'connection_hash': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '40'}),
            'data_source_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '200'}),
            'department': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['services.Department']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'description_fi': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'description_sv': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'divisions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['munigeo.AdministrativeDivision']", 'symmetrical': 'False'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['services.Keyword']", 'symmetrical': 'False'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3067', 'null': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200', 'db_index': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"}),
            'origin_last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '30'}),
            'picture_caption': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200'}),
            'picture_caption_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200'}),
            'picture_caption_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200'}),
            'picture_caption_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200'}),
            'picture_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '200'}),
            'provider_type': ('django.db.models.fields.IntegerField', [], {}),
            'root_services': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'null': 'True', 'max_length': '50'}),
            'services': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['services.Service']", 'symmetrical': 'False'}),
            'street_address': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100'}),
            'street_address_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100'}),
            'street_address_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100'}),
            'street_address_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '100'}),
            'www_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'})
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
            'contact_person': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '50'}),
            'email': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'name_en': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'}),
            'phone': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '50'}),
            'phone_mobile': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '50'}),
            'section': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Unit']", 'related_name': "'connections'"}),
            'www_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'blank': 'True', 'null': 'True', 'max_length': '400'})
        }
    }

    complete_apps = ['services']