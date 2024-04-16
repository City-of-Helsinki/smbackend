"""This module contains utility functions to print reports of the
database contents.

The need is to find examples of extreme or pathological content
with either long field contents or a large amount of related
objects.
"""

from django.db.models import Case, Count, IntegerField, Sum, When
from django.db.models.functions import Length

from services.models import Unit

ESERVICE_LINK_SECTION_TYPE = 9


def unit_description_longest(limit=10):
    qs = (
        Unit.objects.filter(description__isnull=False)
        .annotate(text_len=Length("description"))
        .order_by("-text_len")[:limit]
    )
    return [(u, u.text_len) for u in qs]


def unit_most_services(limit=10):
    qs = Unit.objects.annotate(num_services=Count("services")).order_by(
        "-num_services"
    )[:limit]
    return [(u, u.num_services) for u in qs]


def unit_most_eservice_connections(limit=10):
    # https://stackoverflow.com/questions/30752268/how-to-filter-objects-for-count-annotation-in-django
    units = (
        Unit.objects.filter(connections__section_type=ESERVICE_LINK_SECTION_TYPE)
        .annotate(
            eservice_links=Sum(
                Case(
                    When(connections__section_type=ESERVICE_LINK_SECTION_TYPE, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            )
        )
        .order_by("-eservice_links")[:limit]
    )
    return [(u, u.eservice_links) for u in units]


def unit_most_services_without_periods(limit=10):
    units = (
        Unit.objects.filter(services__period_enabled=False)
        .annotate(
            num_services=Sum(
                Case(
                    When(services__period_enabled=False, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            )
        )
        .order_by("-num_services")[:limit]
    )
    return [(u, u.num_services) for u in units]


def unit_ui_url(unit):
    return "https://palvelukartta.hel.fi/unit/{}".format(unit.id)


def format_unit(unit):
    return "Name: {}\n id: {}\n URL: {}\n".format(
        unit.name_fi, unit.id, unit_ui_url(unit)
    )


def print_units(units):
    for u, value in units:
        print(format_unit(u), "measured value:", value)
        print()
