# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field keywords on 'Service'
        m2m_table_name = db.shorten_name('services_service_keywords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('service', models.ForeignKey(orm['services.service'], null=False)),
            ('keyword', models.ForeignKey(orm['services.keyword'], null=False))
        ))
        db.create_unique(m2m_table_name, ['service_id', 'keyword_id'])


    def backwards(self, orm):
        # Removing M2M table for field keywords on 'Service'
        db.delete_table(db.shorten_name('services_service_keywords'))


    models = {
        'munigeo.administrativedivision': {
            'Meta': {'unique_together': "(('origin_id', 'type', 'parent'),)", 'object_name': 'AdministrativeDivision'},
            'end': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'ocd_id': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'unique': 'True'}),
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
            'type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'unique': 'True'})
        },
        'munigeo.municipality': {
            'Meta': {'object_name': 'Municipality'},
            'division': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'unique': 'True', 'related_name': "'muni'", 'to': "orm['munigeo.AdministrativeDivision']"}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '100', 'blank': 'True'})
        },
        'services.accessibilityvariable': {
            'Meta': {'object_name': 'AccessibilityVariable'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'services.department': {
            'Meta': {'object_name': 'Department'},
            'abbr': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
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
            'id': ('django.db.models.fields.IntegerField', [], {'max_length': '20', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'})
        },
        'services.service': {
            'Meta': {'object_name': 'Service'},
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'identical_to': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'duplicates'", 'to': "orm['services.Service']"}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['services.Keyword']", 'symmetrical': 'False'}),
            'last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'null': 'True', 'related_name': "'children'", 'to': "orm['services.Service']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'unit_count': ('django.db.models.fields.PositiveIntegerField', [], {})
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
            'description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_fi': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_sv': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'divisions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['munigeo.AdministrativeDivision']", 'symmetrical': 'False'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'max_length': '100'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['services.Keyword']", 'symmetrical': 'False'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'srid': '3067'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['munigeo.Municipality']"}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200'}),
            'name_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Organization']"}),
            'origin_last_modified_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '30'}),
            'picture_caption': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200'}),
            'picture_caption_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200', 'blank': 'True'}),
            'picture_caption_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200', 'blank': 'True'}),
            'picture_caption_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '200', 'blank': 'True'}),
            'picture_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '200'}),
            'provider_type': ('django.db.models.fields.IntegerField', [], {}),
            'root_services': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'null': 'True', 'max_length': '50'}),
            'services': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['services.Service']", 'symmetrical': 'False'}),
            'street_address': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100'}),
            'street_address_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100', 'blank': 'True'}),
            'street_address_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100', 'blank': 'True'}),
            'street_address_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100', 'blank': 'True'}),
            'www_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'})
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
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'name_en': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'}),
            'name_fi': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'}),
            'name_sv': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '50'}),
            'phone_mobile': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '50'}),
            'section': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['services.Unit']", 'related_name': "'connections'"}),
            'www_url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400'}),
            'www_url_en': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'}),
            'www_url_fi': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'}),
            'www_url_sv': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '400', 'blank': 'True'})
        }
    }

    complete_apps = ['services']