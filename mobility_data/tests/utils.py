from io import StringIO

from django.core.management import call_command


def import_command(command, *args, **kwargs):
    """
    call_command used when running importer in tests. Parameter command
    is the used import command e.g. "import_payment_zones".
    """
    out = StringIO()
    call_command(
        command,
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
