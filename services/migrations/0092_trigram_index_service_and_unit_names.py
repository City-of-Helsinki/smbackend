from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0091_create_search_view"),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX unit_name_fi_trgm_idx ON services_unit USING GIN (name_fi gin_trgm_ops);
            CREATE INDEX unit_name_sv_trgm_idx ON services_unit USING GIN (name_sv gin_trgm_ops);
            CREATE INDEX unit_name_en_trgm_idx ON services_unit USING GIN (name_en gin_trgm_ops);
            CREATE INDEX service_name_fi_trgm_idx ON services_service USING GIN (name_fi gin_trgm_ops);
            CREATE INDEX service_name_sv_trgm_idx ON services_service USING GIN (name_sv gin_trgm_ops);
            CREATE INDEX service_name_en_trgm_idx ON services_service USING GIN (name_en gin_trgm_ops);
            """,
            reverse_sql="""
            DROP INDEX unit_name_fi_trgm_idx;
            DROP INDEX unit_name_sv_trgm_idx;
            DROP INDEX unit_name_en_trgm_idx;
            DROP INDEX service_name_fi_trgm_idx;
            DROP INDEX service_name_sv_trgm_idx;
            DROP INDEX service_name_en_trgm_idx;
            """,
        ),
    ]
