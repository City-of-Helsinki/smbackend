import json
import requests
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .patch_ssl import get_session

@csrf_exempt
def post_service_request(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    payload = request.POST.copy()
    outgoing = payload.dict()
    if outgoing.get('internal_feedback', False):
        if 'internal_feedback' in outgoing
            del outgoing['internal_feedback']
        api_key = settings.OPEN311['INTERNAL_FEEDBACK_API_KEY']
    else:
        api_key = settings.OPEN311['API_KEY']
    outgoing['api_key'] = api_key
    url = settings.OPEN311['URL_BASE']
    session = get_session()
    r = session.post(url, data=outgoing)
    if r.status_code != 200:
        return HttpResponseBadRequest()

    return HttpResponse(r.content, content_type="application/json")
