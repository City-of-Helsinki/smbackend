import json
import requests
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def post_service_request(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    payload = request.POST.copy()
    payload['api_key'] = settings.OPEN311['API_KEY']
    url = settings.OPEN311['URL_BASE'] + 'requests.json'
    r = requests.post(url, data=payload)

    if r.status_code != 200:
        return HttpResponseBadRequest()

    ret = r.json()
    s = json.dumps(ret)
    return HttpResponse(s, content_type="application/json")
