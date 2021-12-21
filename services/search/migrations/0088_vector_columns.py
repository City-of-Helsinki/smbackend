

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0087_auto_20211221_1248'),
    ]
    operations = [
        migrations.RunSQL(
          
            sql='''
              ALTER TABLE services_unit DROP COLUMN vector_column;
              ALTER TABLE services_service DROP COLUMN vector_column;
              ALTER TABLE services_servicenode DROP COLUMN vector_column;
              ALTER TABLE services_unit ADD COLUMN vector_column tsvector GENERATED ALWAYS AS (
                setweight(to_tsvector('finnish', coalesce(extra, '{}')), 'B') ||
                setweight(to_tsvector('swedish', coalesce(extra, '{}')), 'B') ||
                setweight(to_tsvector('english', coalesce(extra, '{}')), 'B') ||
                
                setweight(to_tsvector('finnish', coalesce(name_fi, '')), 'A') ||
                setweight(to_tsvector('finnish', coalesce(description_fi,'')), 'B') ||
                setweight(to_tsvector('swedish', coalesce(name_sv, '')), 'A') ||
                setweight(to_tsvector('swedish', coalesce(description_sv,'')), 'B') ||
                setweight(to_tsvector('english', coalesce(name_en, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(description_en,'')), 'B')
              ) STORED;

            ALTER TABLE services_service ADD COLUMN vector_column tsvector GENERATED ALWAYS AS (
                setweight(to_tsvector('finnish', coalesce(name_fi, '')), 'A') ||
                setweight(to_tsvector('swedish', coalesce(name_sv, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(name_en, '')), 'A')
            ) STORED;
        
            ALTER TABLE services_servicenode ADD COLUMN vector_column tsvector GENERATED ALWAYS AS (
                setweight(to_tsvector('finnish', coalesce(name_fi, '')), 'A') ||
                setweight(to_tsvector('swedish', coalesce(name_sv, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(name_en, '')), 'A')
            ) STORED;
        
            ''',

            reverse_sql = '''
              ALTER TABLE services_unit DROP COLUMN vector_column;
              ALTER TABLE services_service DROP COLUMN vector_column;
              ALTER TABLE services_servicenode DROP COLUMN vector_column;
            '''
        ),
    ]



