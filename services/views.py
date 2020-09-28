import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.exceptions import ParseError

from .search_suggestions import get_suggestions

LANGUAGES = [x[0] for x in settings.LANGUAGES]


@require_http_methods(["GET", "POST"])
def suggestion(request):
    query = request.GET["q"]
    if not query:
        return HttpResponseBadRequest()
    lang_code = request.GET.get("language", LANGUAGES[0])
    if lang_code not in LANGUAGES:
        raise ParseError(
            "Invalid language supplied. Supported languages: %s" % ",".join(LANGUAGES)
        )
    return JsonResponse(
        get_suggestions(query, lang_code), content_type="application/json"
    )


@csrf_exempt
@require_http_methods(["POST"])
def post_service_request(request):
    payload = request.POST.copy()
    outgoing = payload.dict()
    if outgoing.get("internal_feedback", False):
        if "internal_feedback" in outgoing:
            del outgoing["internal_feedback"]
        api_key = settings.OPEN311["INTERNAL_FEEDBACK_API_KEY"]
    else:
        api_key = settings.OPEN311["API_KEY"]
    outgoing["api_key"] = api_key
    url = settings.OPEN311["URL_BASE"]
    session = requests.Session()

    # Modify parameters for request in case of City of Turku
    if "smbackend_turku" in settings.INSTALLED_APPS:
        outgoing.pop("service_request_type")
        outgoing.pop("can_be_published")
        outgoing["address_string"] = "null"
        outgoing["service_code"] = settings.OPEN311["SERVICE_CODE"]

    r = session.post(url, data=outgoing)
    if r.status_code != 200:
        return HttpResponseBadRequest()

    return HttpResponse(r.content, content_type="application/json")
