from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("munigeo", "0010_postalcodearea_address_full_name_en_and_more"),
        ("services", "0121_make_requeststatistic_timeframe_unique"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_address'
                      AND column_name = 'full_name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_address'
                      AND column_name = 'full_name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_address
                        SET full_name_fi = full_name
                        WHERE full_name IS NOT NULL
                          AND full_name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_administrativedivision'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_administrativedivision'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_administrativedivision
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_municipality'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_municipality'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_municipality
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_postalcodearea'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_postalcodearea'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_postalcodearea
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_street'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_street'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_street
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;
            END
            $$;

            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conrelid = 'public.munigeo_street'::regclass
                      AND conname =
                        'munigeo_street_municipality_id_name_fi_1c84aabc_uniq'
                ) THEN
                    EXECUTE '
                        ALTER TABLE public.munigeo_street
                        ADD CONSTRAINT
                            munigeo_street_municipality_id_name_fi_1c84aabc_uniq
                        UNIQUE (municipality_id, name_fi)
                    ';
                END IF;
            END
            $$;

            ALTER TABLE public.munigeo_address
                DROP COLUMN IF EXISTS full_name;
            ALTER TABLE public.munigeo_administrativedivision
                DROP COLUMN IF EXISTS name;
            ALTER TABLE public.munigeo_municipality
                DROP COLUMN IF EXISTS name;
            ALTER TABLE public.munigeo_postalcodearea
                DROP COLUMN IF EXISTS name;
            ALTER TABLE public.munigeo_street
                DROP COLUMN IF EXISTS name;
            ALTER TABLE public.munigeo_street
                DROP CONSTRAINT IF EXISTS
                    munigeo_street_municipality_id_name_6e998d56_uniq;

            CREATE OR REPLACE FUNCTION public.naturalsort(text)
            RETURNS bytea
            LANGUAGE sql
            IMMUTABLE STRICT
            AS $function$
                                select string_agg(convert_to(coalesce(r[2],
                                length(length(r[1])::text) || length(r[1])::text || r[1]),
                                'SQL_ASCII'),'\\x00')
                                from regexp_matches($1, '0*([0-9]+)|([^0-9]+)', 'g') r;
                            $function$;
            """,
            # The ramp is one-way; its dropped columns cannot be reconstructed.
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
