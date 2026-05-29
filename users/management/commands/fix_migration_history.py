from django.core.management.base import BaseCommand
from django.db import OperationalError, ProgrammingError, connection
from django.utils.timezone import now


class Command(BaseCommand):
    help = (
        "Fix inconsistent migration history that occurs in review environments whose "
        "databases were seeded before the custom 'users' app was introduced. "
        "If admin.0001_initial is recorded as applied but users.0001_initial is not, "
        "the users migration is faked so that 'manage.py migrate' can proceed."
    )

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations "
                    "WHERE app = 'admin' AND name = '0001_initial'"
                )
                admin_applied = cursor.fetchone()[0]

                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations "
                    "WHERE app = 'users' AND name = '0001_initial'"
                )
                users_applied = cursor.fetchone()[0]

                table_names = connection.introspection.table_names(cursor)
                auth_user_exists = "auth_user" in table_names

            if admin_applied and not users_applied and auth_user_exists:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO django_migrations (app, name, applied) "
                        "VALUES (%s, %s, %s)",
                        ["users", "0001_initial", now()],
                    )
                self.stdout.write(
                    self.style.SUCCESS(
                        "Fixed migration history: faked users.0001_initial. "
                        "The database was seeded before the custom users app existed."
                    )
                )
            elif admin_applied and not users_applied and not auth_user_exists:
                self.stdout.write(
                    self.style.WARNING(
                        "admin.0001_initial is applied but auth_user table is missing "
                        "— skipping fake to avoid hiding a corrupted database state."
                    )
                )
            else:
                self.stdout.write("Migration history is consistent, no fix needed.")

        except (OperationalError, ProgrammingError):
            # django_migrations table does not exist yet (fresh database).
            # No inconsistency to fix; the normal migrate run will handle everything.
            self.stdout.write(
                "django_migrations table not found — fresh database, no fix needed."
            )
