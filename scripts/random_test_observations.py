#!/usr/bin/env python
import requests
import sys
import json
import random

values = {
    33418: {'ice_skating_field_condition': ['closed', 'plowed', 'frozen', 'freezing_started']},
    33483: {'ski_trail_condition':
            ['closed',
             'good',
             'satisfactory',
             'poor',
             'snowless',
             'event',
             'littered',
             'groomed',
             'snowmaking'],
            'ski_trail_maintenance':
            ['maintenance_finished']}}

def main(base_url):
    for service, vals in values.items():
       response = requests.get(
           base_url + '/unit/?service={}&only=id&page_size=1000'.format(service))
       assert response.status_code == 200
       fields = response.json()
       unit_ids = [u['id'] for u in fields['results']]
       for prop, v in vals.items():
           for uid in unit_ids:
               response = requests.post(
                   base_url + '/observation/',
                   data=dict(
                       value=random.choice(v),
                       property=prop,
                       unit=uid
                   ))
               if response.status_code != 201:
                   print('error')
                   sys.stderr.write(response.text)
                   exit(1)

if __name__ == '__main__':
    base_url = sys.argv[1]
    main(base_url)
