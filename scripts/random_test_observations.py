#!/usr/bin/env python
import requests
import sys
import json
import random

values = ['closed', 'plowing', 'freezing', 'freezing_started']

def main(base_url):
    response = requests.get(
        base_url + '/unit/?service=33418&only=id&page_size=1000')
    assert response.status_code == 200
    fields = response.json()
    unit_ids = [u['id'] for u in fields['results']]
    for uid in unit_ids:
        response = requests.post(
            base_url + '/observation/',
            data=dict(
                value=random.choice(values),
                property='ice_skating_field_condition',
                unit=uid
        ))
        assert response.status_code == 201

if __name__ == '__main__':
    base_url = sys.argv[1]
    main(base_url)
