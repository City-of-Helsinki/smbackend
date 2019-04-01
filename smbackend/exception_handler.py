import json

from django.db.utils import InternalError
from django.http.response import HttpResponseBadRequest
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc, context):

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    json_resp = json.dumps(response.data) if response else exc

    if isinstance(exc, ValidationError):
        return HttpResponseBadRequest(content=json.dumps('ValidationError: {}'.format(json_resp)),
                                      content_type='application/json')

    if isinstance(exc, InternalError):
        return HttpResponseBadRequest(content=json.dumps('Database Error: {}'.format(json_resp)),
                                      content_type='application/json')

    if isinstance(exc, ValueError):
        return HttpResponseBadRequest(content=json.dumps('ValueError: {}'.format(json_resp)),
                                      content_type='application/json')

    return response
