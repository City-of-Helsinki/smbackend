import os

import pytest
import requests_mock
from django.core.management import call_command
from django.utils.six import StringIO

from services.management.commands.services_import_v4 import URL_BASE as TPR_URL
from services.models import Unit

TPR_MOCK_DIR = os.path.join(os.path.dirname(__file__), 'tpr_mock_data')

# @pytest.fixture(scope="module")
# def smtp():
#     return smtplib.SMTP("smtp.gmail.com")


@pytest.mark.django_db
def test_unit_updating():
    """ This test requires a fixture for munigeo. Generate one with:
        $ ./manage.py dumpdata --format=json --indent=2 > smbackend/test/fixtures/munigeo.json
        Also to moch the TPR API we need to include the response content. Generate the responses by running the
        included script:
        $ python generate_tpr_mock_data.py """
    with requests_mock.Mocker() as mock:
        call_command('loaddata', 'smbackend/test/fixtures/munigeo.json')
        mock_tpr(mock)
        assert Unit.objects.count() == 0
        out = StringIO()
        call_command('services_import', traceback=True, organizations=True,
                     departments=True, services=True, units=True, stdout=out)
        assert Unit.objects.count() > 0


def mock_tpr(mock):
    endpoints = ['connection', 'unit', 'organization', 'service', 'accessibility_property', 'department']
    for endpoint in endpoints:
        mock.register_uri('GET',
                          '%s%s/' % (TPR_URL, endpoint),
                          text=open(os.path.join(TPR_MOCK_DIR, '%s.json' % endpoint)).read(),
                          status_code=200)
