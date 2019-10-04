import requests
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .search_suggestions import get_suggestions


@require_http_methods(['GET', 'POST'])
def suggest(request):
    query = request.GET['q']
    if not query:
        return HttpResponseBadRequest()
    return JsonResponse(get_suggestions(query), content_type='application/json')


@csrf_exempt
@require_http_methods(['POST'])
def post_service_request(request):
    payload = request.POST.copy()
    outgoing = payload.dict()
    if outgoing.get('internal_feedback', False):
        if 'internal_feedback' in outgoing:
            del outgoing['internal_feedback']
        api_key = settings.OPEN311['INTERNAL_FEEDBACK_API_KEY']
    else:
        api_key = settings.OPEN311['API_KEY']
    outgoing['api_key'] = api_key
    url = settings.OPEN311['URL_BASE']
    session = requests.Session()
    r = session.post(url, data=outgoing)
    if r.status_code != 200:
        return HttpResponseBadRequest()

    return HttpResponse(r.content, content_type='application/json')
