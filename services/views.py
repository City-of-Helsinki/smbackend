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
    outgoing['api_key'] = settings.OPEN311['API_KEY']
    url = settings.OPEN311['URL_BASE']
    session = get_session()
    r = session.post(url, data=outgoing)
    if r.status_code != 200:
        return HttpResponseBadRequest()

    return HttpResponse(r.content, content_type="application/json")
