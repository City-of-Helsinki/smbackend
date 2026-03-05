from django.db import migrations


class Migration(migrations.Migration):
    """
    Manually set maintenance_organization and the manual_maintenance_organization
    guard flag for units that must not have their maintenance_organization overwritten
    by the municipality name during imports.
    """

    dependencies = [
        ("services", "0119_update_search_view"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE services_unit
                SET extensions = COALESCE(extensions, ''::hstore)
                    || hstore('manual_maintenance_organization', 'True')
                    || hstore('maintenance_organization', 'helsinki')
                WHERE id IN (65014, 50984, 53994, 53993);
            """,
            reverse_sql="""
                UPDATE services_unit
                SET extensions = extensions
                    - 'manual_maintenance_organization'::text
                WHERE id IN (65014, 50984, 53994, 53993);
            """,
        ),
    ]
