# -*- coding: utf-8 -*-
from builtins import getattr

import psycopg2

from django.core.management.base import BaseCommand
from observations.models import ObservableProperty


class Command(BaseCommand):
    conn = psycopg2.connect("dbname=targetdb user=smbackend password=smbackend host=localhost")
    cur = conn.cursor()

    def handle(self, **options):
        self.cur.execute('SELECT * FROM observations_observableproperty_v1;')
        props = self.cur.fetchall()

        for line in props:
            property_id = line[0]
            name = line[1]
            measurement_unit = line[2]
            observation_type = line[3]

            self.insert(property_id, name, measurement_unit, observation_type)
        self.add_service()

    def insert(self, property_id, name, measurement_unit, observation_type):

        errors = dict.fromkeys(['property_id'])

        try:
            property_v2 = ObservableProperty.objects.filter(id=property_id).values('id')
            if len(property_v2) == 0:
                ObservableProperty.objects.create(id=property_id, name=name,
                                                                measurement_unit=measurement_unit,
                                                                observation_type=observation_type)
        except Exception as e:
            print('could not create ObservableProperty, ', e)
            errors['property_id'] = property_id

    def add_service(self):
        for obs_prop in ObservableProperty.objects.all():
            self.cur.execute(
                'select service_id from observations_observableproperty_services_v1 where observableproperty_id=%s;',
                (getattr(obs_prop, 'id'),))
            services = self.cur.fetchall()
            codes = {33417: 695, 33418: 406, 33419: 235, 33420: 514, 33421: 407, 33483: 191, 33492: 318, 33467: 731,
                     33468: 730, 33466: 426}
            for service in services:
                obs_prop.services.add(codes[service[0]])
