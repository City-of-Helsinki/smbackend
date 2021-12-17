from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('services', '0087_auto_20211216_1102'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
              ALTER TABLE services_unit ADD COLUMN vector_column tsvector GENERATED ALWAYS AS (
                setweight(to_tsvector('finnish', coalesce(name_fi, '')), 'A') ||
                setweight(to_tsvector('finnish', coalesce(description_fi,'')), 'B')
              ) STORED;
            ''',

            reverse_sql = '''
              ALTER TABLE services_unit DROP COLUMN vector_column;
            '''
        ),
    ]