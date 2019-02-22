import json
from django.http.response import HttpResponseBadRequest
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, ParseError


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    json_resp = json.dumps(response.data)

    if isinstance(exc, ValidationError):
        response.status_code = 400
        return HttpResponseBadRequest(content=json_resp,
                                      content_type='application/json')
    if isinstance(exc, ParseError):
        response.status_code = 400
        return HttpResponseBadRequest(content=json_resp,
                                      content_type='application/json')
    if isinstance(exc, ValueError):
        response.status_code = 400
        return HttpResponseBadRequest(content=json_resp)
    return response
