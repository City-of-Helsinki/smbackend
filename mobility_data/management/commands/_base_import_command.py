from django.core.management import BaseCommand


class BaseImportCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--test-mode",
            nargs="+",
            default=False,
            help="Run script in test mode.",
        )
