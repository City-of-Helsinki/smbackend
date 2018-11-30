# -*- coding: utf-8 -*-
import psycopg2

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from observations.models import PluralityAuthToken
from django.core.management import call_command
from . import user_import


class Command(BaseCommand):
    conn = psycopg2.connect("dbname=targetdb user=smbackend password=smbackend host=localhost")
    cur = conn.cursor()

    def handle(self, **options):

        User.objects.all().delete()
        self.users()

        PluralityAuthToken.objects.all().delete()
        self.cur.execute('SELECT * FROM observations_pluralityauthtoken_v1;')
        tokens = self.cur.fetchall()

        for line in tokens:
            key = line[1]
            created = line[2]
            active = line[3]
            user_id = line[4]

            self.insert(key, created, active, user_id)

    def insert(self, key, created, active, user_id):

        errors = dict.fromkeys(['user_id'])

        self.cur.execute('SELECT username FROM auth_user WHERE id=%s;', (user_id,))
        user = self.cur.fetchone()[0]
        print(user)

        try:
            user_id = User.objects.filter(username=user).values('id')[0]['id']
            print(user_id)
            authtoken = PluralityAuthToken.objects.create(key=key, created=created, active=active, user_id=user_id)
        except Exception as e:
            print()
            print('could not create PluralityAuthToken, ', e)
            errors['user_id'] = user

    def users(self):
        # populate auth_user taulu


        self.cur.execute('SELECT * FROM auth_user;')
        users = self.cur.fetchall()
        print(users)
        self.cur.execute('select * from auth_user limit 0;')
        colnames = [desc[0] for desc in self.cur.description]
        print(colnames)

        for user in users:
            # get entry from user_auth v1 by id
            self.cur.execute('select * from auth_user where id=%s', (user[0],))
            user_entry = self.cur.fetchone()

            # populate string with field values for inserting into allowed_value
            #create_str = ''
            username = ''
            password = ''
            city = ''
            for i in range(len(colnames)):
                #if colnames[i] != 'id':
                    # v2 model required not null for 'last_login'
                    # if colnames[i] == 'last_login':
                    #     create_str = create_str + colnames[i] + "='2018-01-01 00:00',"
                    #     continue
                if colnames[i] == 'username':
                    username = user_entry[i]
                    print(username)
                    city = user_entry[i].split('liiku')[0]
                    print(city)
                if colnames[i] == 'password':
                    password = user_entry[i]
                    print(password)
                    #create_str = create_str + colnames[i] + "='" + str(user_entry[i]) + "',"
            try:
                call_command('user_import', username, password, city)

                #eval('User.objects.create(' + create_str[:-1] + ')')
            except Exception as e:
                print('wat?', e)
                continue
                # get new auth_user id from v2
                user = User.objects.get(username=username)
                print('new user', user)
