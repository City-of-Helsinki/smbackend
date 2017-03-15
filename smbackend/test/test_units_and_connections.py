import os

import pytest
import requests
import requests_mock
from django.core.management import call_command
from django.utils.six import StringIO

from services.management.commands.services_import import URL_BASE as TPR_URL
from services.management.commands.services_import import Command as ServiceImportCommand
# TPR_URL = "www.hel.fi/palvelukarttaws/rest/v4/"
from services.models import Unit

TPR_MOCK_DIR = os.path.join(os.path.dirname(__file__), 'tpr_mock_data')

@pytest.fixture(scope="module")
def smtp():
    return smtplib.SMTP("smtp.gmail.com")


@pytest.mark.django_db
def test_unit_updating():
    with requests_mock.Mocker() as mock:
        call_command('loaddata', 'smbackend/test/fixtures/munigeo.json')
        mock_tpr(mock)
        # response = requests.get('http://www.hel.fi/palvelukarttaws/rest/v3/connection/')
        # assert 'paivahoito-ja-koulutus' in response.text
        assert Unit.objects.count() == 0
        # cmd = ServiceImportCommand()
        # cmd.verbosity = 0
        # cmd.import_units()
        out = StringIO()
        call_command('services_import', traceback=True, organizations=True, departments=True, services=True, units=True, stdout=out)
        assert Unit.objects.count() > 0


def mock_tpr(mock):
    endpoints = ['connection', 'unit', 'organization', 'service', 'accessibility_property', 'department']
    for endpoint in endpoints:
        mock.register_uri('GET',
                          '%s%s/' % (TPR_URL, endpoint),
                          text=open(os.path.join(TPR_MOCK_DIR, '%s.json' % endpoint)).read(),
                          status_code=200)
