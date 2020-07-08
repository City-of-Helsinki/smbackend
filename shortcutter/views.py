from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import redirect


class HttpResponseNotImplemented(HttpResponse):
    status_code = 501


def unit_short_url(request, unit_id):
    unit_url = getattr(settings, 'SHORTCUTTER_UNIT_URL', None)
    if not unit_url:
        return HttpResponseNotImplemented()

    return redirect(unit_url.format(id=unit_id))
