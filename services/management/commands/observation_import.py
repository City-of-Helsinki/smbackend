# -*- coding: utf-8 -*-
import psycopg2

from django.core.management.base import BaseCommand
from services.models import Unit
from observations.models import AllowedValue, ObservableProperty, Observation, PluralityAuthToken,\
    DescriptiveObservation, CategoricalObservation


class Command(BaseCommand):
    conn = psycopg2.connect("dbname=targetdb user=smbackend password=smbackend host=localhost")
    cur = conn.cursor()

    def handle(self, **options):
        Observation.objects.all().delete()
        CategoricalObservation.objects.all().delete()
        DescriptiveObservation.objects.all().delete()

        self.cur.execute('SELECT * FROM observations_observation_v1;')
        observations = self.cur.fetchall()

        for line in observations:
            time = line[1]
            polymorphic_ctype_id = line[2]
            observable_property = line[3]
            unit_id = line[4]
            allowed_value = line[6]
            auth_id = line[5]

            self.insert(time, polymorphic_ctype_id, observable_property, unit_id, allowed_value, auth_id)

    def insert(self, time, polymorphic_ctype_id, observable_property, unit_id, allowed_value, auth_id):
        errors = dict.fromkeys(['unit','allowed_value','observable_property','auth_id'])

        # unit #
        self.cur.execute('select id,name from services_unit where id=%s', (unit_id,))
        unit_id = self.cur.fetchone()
        print(unit_id)

        try:
            unit_obj = Unit.objects.get(id=unit_id[0])
            if unit_obj is None:
                unit_obj = Unit.objects.get(name=unit_id[1])
        except Exception as e:
            print('unit id not found. ', e)
            errors['unit'] = unit_id
            return False
        print(unit_obj)

        # observable property #
        try:
            property_obj = ObservableProperty.objects.get(id=observable_property)
        except Exception as e:
            print('observable property not found.',e)
            errors['observable_property'] = observable_property
            return False

        # allowed_value #

        # get name of allowed value from v1 by id
        self.cur.execute('select name from observations_allowedvalue_v1 where id=%s', (allowed_value,))
        allowed_name = self.cur.fetchone()
        print(allowed_name)

        if allowed_name == (None,) or allowed_name is None:
            return False

        try:
            # get id of allowed value from v2 by name
            allowed_obj = AllowedValue.objects.get(name=allowed_name[0], property=property_obj)
        except Exception as e:
            print('allowed value not found', e)

            # if allowed_name is not None:
            # get columns of allowed_value table
            self.cur.execute('select * from observations_allowedvalue_v1 limit 0;')
            colnames = [desc[0] for desc in self.cur.description]

            # get field of allowed value_from v1 by id
            self.cur.execute('select * from observations_allowedvalue_v1 where id=%s', (allowed_value,))
            allowed_field = self.cur.fetchone()

            # populate string with field values for inserting into allowed_value
            create_str = ''
            for i in range(len(colnames)):
                create_str = create_str + colnames[i] + "='" + str(allowed_field[i]) + "',"
            print(create_str[:-1])
            eval('AllowedValue.objects.create(' + create_str[:-1] + ')')

            # get new allowed_value id from v2
            allowed_obj = AllowedValue.objects.get(name=allowed_name[0], property=property_obj)

        # PluralityAuthToken #
        try:
            auth_obj = PluralityAuthToken.objects.get(id=auth_id)
        except Exception as e:
            print('PluralityAuthToken not found', e)
            errors['auth_id'] = auth_id
            return False

        # create observation
        if (unit_obj, allowed_obj, property_obj, auth_obj) is not None:
            try:
                if 'descriptive' in getattr(property_obj, 'observation_type').lower():
                    obs = DescriptiveObservation.objects.create(unit=unit_obj, value=allowed_obj, time=time, auth=auth_obj, property=property_obj)
                elif 'categorical' in getattr(property_obj, 'observation_type').lower():
                    obs = CategoricalObservation.objects.create(unit=unit_obj, value=allowed_obj, time=time, auth=auth_obj, property=property_obj)
            except Exception as e:
                print('could not create observation', e)
                return False
            print(obs)
