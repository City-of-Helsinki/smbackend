from django.conf import settings
from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand, CommandError
from django.utils import translation
from haystack.query import SearchQuerySet
from munigeo.models import Address, AdministrativeDivision

from services.models import Service, Unit
from services.search_indexes import AdministrativeDivisionIndex

LANGUAGES = [l[0] for l in settings.LANGUAGES]


def _check_index_integrity(model):
    errors = []
    # Unit._meta.label_lower

    def format_error(model=None, public=None, db=None, index=None, language=None):
        return ("Differing count for language {language} model {model} "
                "with public=={public}, db: {db}, index: {index}").format(
                    model=model, public=public, db=db, index=index, language=language)

    for language in LANGUAGES:
        with translation.override(language):
            for public in [True, False]:
                qs = None
                try:
                    qs = model.objects.filter(public=public)
                except FieldError:
                    if public is True:
                        qs = model.objects.all()
                    else:
                        qs = model.objects.none()
                if model == AdministrativeDivision:
                    qs = qs.filter(type__in=AdministrativeDivisionIndex.indexed_types())
                db_count = qs.count()
                haystack_count = SearchQuerySet().filter(
                    django_ct=model._meta.label_lower).filter(public=str(public).lower()).count()
                if db_count != haystack_count:
                    errors.append(format_error(model=model, db=db_count, language=language,
                                               index=haystack_count, public=public))
    return errors


class Command(BaseCommand):
    help = """ Verify that the amount of documents indexed
    in elasticsearch matches the expected amount. """

    def handle(self, *args, **options):
        errors = dict(((model._meta.label_lower, _check_index_integrity(model)) for model in [
            Unit, Service, Address, AdministrativeDivision]))
        if len(errors):
            error_strings = ["Integrity errors"]
            for key, value in errors.items():
                if len(value):
                    error_strings.append("{}\n{}".format(key, "\n".join(value)))
                    raise CommandError("\n\n".join(error_strings))
