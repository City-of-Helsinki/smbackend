from django.http.response import HttpResponseBadRequest
import json
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, ParseError


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if isinstance(exc, ValidationError):
        response.status_code = 400
        return HttpResponseBadRequest(content=json.dumps(response.data),
                                      content_type='application/json')
    if isinstance(exc, ParseError):
        response.status_code = 400
        return HttpResponseBadRequest(content=json.dumps(response.data),
                                      content_type='application/json')
    return response
