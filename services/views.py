import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone as tz
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status

from services.models import FeedbackMapping, RequestStatistic, Unit
from services.models.feedback import DEFAULT_SERVICE_CODE


# TODO: Remove this once the new Open311 service is enabled to production
def use_legacy_params(data):
    if data.get("internal_feedback", False):
        if "internal_feedback" in data:
            del data["internal_feedback"]
        api_key = settings.OPEN311["INTERNAL_FEEDBACK_API_KEY"]
    else:
        api_key = settings.OPEN311["API_KEY"]
    data["api_key"] = api_key


def _resolve_feedback_service_code(unit_department) -> str:
    mapping = FeedbackMapping.objects.filter(department=unit_department)
    if not mapping:
        if unit_department.parent:
            return _resolve_feedback_service_code(unit_department.parent)
        else:
            return DEFAULT_SERVICE_CODE
    return mapping.first().service_code


@csrf_exempt
@require_http_methods(["POST"])
def post_service_request(request):
    payload = request.POST.copy()
    data = payload.dict()

    if settings.OPEN311["NEW_SERVICE_ENABLED"]:
        try:
            unit_id = int(data.get("service_object_id", 0))
        except ValueError:
            unit_id = 0
        if unit_id:
            data["service_object_type"] = "unit"
            try:
                unit_department = Unit.objects.get(pk=unit_id).department
                if unit_department:
                    data["service_code"] = _resolve_feedback_service_code(
                        unit_department
                    )
            except ObjectDoesNotExist:
                data["service_code"] = DEFAULT_SERVICE_CODE
                unit_id = 0
        if not unit_id:
            if "service_object_id" in data:
                del data["service_object_id"]
            if "service_object_type" in data:
                del data["service_object_type"]
        service_code = data.get("service_code", 0)
        if not service_code:
            data["service_code"] = DEFAULT_SERVICE_CODE
        data["api_key"] = settings.OPEN311["API_KEY"]
    else:
        use_legacy_params(data)

    url = settings.OPEN311["URL_BASE"]
    session = requests.Session()

    r = session.post(url, data=data)
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
