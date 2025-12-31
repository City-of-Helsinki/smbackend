from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0118_servicenode_services_servicenode_tree_fc8f"),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE VIEW search_view
                AS SELECT concat('unit_', services_unit.id) AS id,
                    services_unit.name_fi,
                    services_unit.name_sv,
                    services_unit.name_en,
                    services_unit.search_column_fi,
                    services_unit.search_column_sv,
                    services_unit.search_column_en,
                    'Unit'::text AS type_name
                   FROM services_unit where services_unit.is_active = true
                UNION
                 SELECT concat('service_', services_service.id) AS id,
                    services_service.name_fi,
                    services_service.name_sv,
                    services_service.name_en,
                    services_service.search_column_fi,
                    services_service.search_column_sv,
                    services_service.search_column_en,
                    'Service'::text AS type_name
                   FROM services_service
                union
                 SELECT concat('servicenode_', string_agg(id::text, '_')) AS ids,
                    services_servicenode.name_fi,
                    services_servicenode.name_sv,
                    services_servicenode.name_en,
                    services_servicenode.search_column_fi,
                    services_servicenode.search_column_sv,
                    services_servicenode.search_column_en,
                    'ServiceNode'::text AS type_name
                   FROM services_servicenode group by 2,3,4,5,6,7,8
                UNION
                 SELECT concat('administrativedivision_', munigeo_administrativedivision.id) AS id,
                    munigeo_administrativedivision.name_fi,
                    munigeo_administrativedivision.name_sv,
                    munigeo_administrativedivision.name_en,
                    munigeo_administrativedivision.search_column_fi,
                    munigeo_administrativedivision.search_column_sv,
                    munigeo_administrativedivision.search_column_en,
                    'AdministrativeDivision'::text AS type_name
                   FROM munigeo_administrativedivision
                UNION
                 SELECT concat('address_', munigeo_address.id) AS id,
                    munigeo_address.full_name_fi AS name_fi,
                    munigeo_address.full_name_sv AS name_sv,
                    munigeo_address.full_name_en AS name_en,
                    munigeo_address.search_column_fi,
                    munigeo_address.search_column_sv,
                    munigeo_address.search_column_en,
                    'Address'::text AS type_name
                   FROM munigeo_address;
            """,
            reverse_sql="""
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
        ),
    ]
