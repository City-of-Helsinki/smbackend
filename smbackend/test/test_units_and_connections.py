import os

import requests
import requests_mock

from services.management.commands.services_import import URL_BASE as TPR_URL
# TPR_URL = "www.hel.fi/palvelukarttaws/rest/v4/"
TPR_MOCK_DIR = os.path.join(os.path.dirname(__file__), 'tpr_mock_data')


def test_unit_updating():
    with requests_mock.Mocker() as mock:
        mock_tpr(mock)
        response = requests.get('http://www.hel.fi/palvelukarttaws/rest/v3/connection/')
        assert 'paivahoito-ja-koulutus' in response.text


def mock_tpr(mock):
    endpoints = ['connection', 'unit', 'organization', 'service', 'accessibility_property']
    for endpoint in endpoints:
        mock.register_uri('GET',
                          '%s%s/' % (TPR_URL, endpoint),
                          text=open(os.path.join(TPR_MOCK_DIR, '%s.json' % endpoint)).read(),
                          status_code=200)
