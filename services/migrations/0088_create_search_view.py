from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0087_create_search_columns"),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE VIEW search_view as
            SELECT concat('unit_', services_unit.id) AS id, name_fi, name_sv, name_en, search_column, 'Unit' AS type_name from services_unit
            UNION
            SELECT concat('service_', id) AS id, name_fi, name_sv, name_en, search_column, 'Service' AS type_name from services_service
            UNION
            SELECT concat('servicenode_', id) AS id, name_fi, name_sv, name_en, search_column, 'ServiceNode' AS type_name from services_servicenode
            UNION
            SELECT concat('administrativedivision_', id) AS id,  name_fi, name_sv, name_en, search_column, 'AdministrativeDivision' AS type_name from munigeo_administrativedivision
            UNION
            SELECT concat('address_', id) AS id,  full_name_fi as name_fi, full_name_sv as name_sv, full_name_en as name_en, search_column, 'Address' AS type_name from munigeo_address;
            """,
            reverse_sql="""
            DROP VIEW search_view;
            """,
        ),
    ]
