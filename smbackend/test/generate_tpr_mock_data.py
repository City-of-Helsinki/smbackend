"""
Downloads a full set from TPR and saves the results in to json files that can be used
to mock the TPR API in tests.
"""
import os
import requests

TPR_URL = 'http://www.hel.fi/palvelukarttaws/rest/v3/'
TPR_MOCK_DIR = os.path.join(os.path.dirname(__file__), 'tpr_mock_data')

if __name__ == '__main__':
    print("Generating mock data for the TPR tests")
    endpoints = ['connection', 'unit', 'organization', 'service', 'accessibility_property', 'department']
    for endpoint in endpoints:
        response = requests.get('%s%s/' % (TPR_URL, endpoint))
        with open(os.path.join(TPR_MOCK_DIR, '%s.json' % endpoint), 'wt') as fh:
            fh.write(response.text)
            print("  --> ", endpoint, ' - ', len(response.content), 'bytes')
