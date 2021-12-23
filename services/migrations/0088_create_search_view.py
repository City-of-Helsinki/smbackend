

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0087_auto_20211222_0954'),
    ]
    operations = [
        migrations.RunSQL(          
            sql='''
            CREATE VIEW search_view as
            SELECT concat('unit_', services_unit.id) AS id, name_fi, name_sv, name_en, vector_column, 'Unit' AS type_name from services_unit
            UNION
            SELECT concat('service_', id) AS id, name_fi, name_sv, name_en, vector_column, 'Service' AS type_name from services_service
            UNION
            SELECT concat('servicenode_', id) AS id,  name_fi, name_sv, name_en, vector_column, 'ServiceNode' AS type_name from services_servicenode;
            ''',
            reverse_sql = '''
            DROP VIEW search_view;
            '''
        ),
    ]


