import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone as tz
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status

from services.models.statistic import RequestStatistic


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


@csrf_exempt
@require_http_methods(["POST"])
def post_statistic(request):
    payload = request.POST.copy()
    data = payload.dict()
    now = tz.now()
    timeframe = "%s/%s" % (now.month, now.year)
    statistic, _ = RequestStatistic.objects.get_or_create(timeframe=timeframe)
    statistic.request_counter += 1

    if "embed" in data and data["embed"]:
        statistic.details["embed"] += 1

    if "mobile_device" in data and data["mobile_device"]:
        statistic.details["mobile_device"] += 1

    statistic.save()

    return HttpResponse(status=status.HTTP_201_CREATED, content_type="application/json")
