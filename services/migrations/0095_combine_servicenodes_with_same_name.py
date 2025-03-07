from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0094_update_search_view"),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW search_view as
            SELECT concat('unit_', services_unit.id) AS id, name_fi, name_sv, name_en, search_column_fi, search_column_sv, search_column_en, 'Unit' AS type_name from services_unit
            UNION
            SELECT concat('service_', id) AS id, name_fi, name_sv, name_en, search_column_fi, search_column_sv, search_column_en, 'Service' AS type_name from services_service
            UNION
            SELECT concat('servicenode_', string_agg(id::text, '_')) AS ids, name_fi, name_sv, name_en, search_column_fi, search_column_sv, search_column_en, 'ServiceNode' AS type_name from services_servicenode group by 2,3,4,5,6,7,8
            UNION
            SELECT concat('administrativedivision_', id) AS id,  name_fi, name_sv, name_en, search_column_fi, search_column_sv, search_column_en, 'AdministrativeDivision' AS type_name from munigeo_administrativedivision
            UNION
            SELECT concat('address_', id) AS id,  full_name_fi as name_fi, full_name_sv as name_sv, full_name_en as name_en, search_column_fi, search_column_sv, search_column_en, 'Address' AS type_name from munigeo_address;
            """,
            reverse_sql="""
            DROP VIEW search_view;
            """,
        ),
    ]
