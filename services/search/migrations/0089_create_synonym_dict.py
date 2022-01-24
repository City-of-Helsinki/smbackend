from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0088_create_search_view"),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TEXT SEARCH CONFIGURATION finnish OWNER TO servicemap;
            CREATE TEXT SEARCH DICTIONARY smbackend_fi_sym (
                TEMPLATE = synonym,
                SYNONYMS = smbackend_fi_sym
            );
            ALTER TEXT SEARCH CONFIGURATION finnish
                ALTER MAPPING FOR asciiword
                WITH smbackend_fi_sym, finnish_stem;
            """,
            reverse_sql="""
            ALTER TEXT SEARCH CONFIGURATION finnish  DROP MAPPING FOR asciiword;
            DROP TEXT SEARCH DICTIONARY smbackend_fi_sym;            
            """,
        ),
    ]