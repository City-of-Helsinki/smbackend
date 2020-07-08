# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from observations.models import UserOrganization
from services.models import Department


class Command(BaseCommand):
    help = "Import users, manage.py user_import username password city"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('city')

    def handle(self, **options):
        # city codes:
        # espoo:        520a4492-cb78-498b-9c82-86504de88dce
        # helsinki:     83e74666-0836-4c1d-948a-4b34a8b90301
        # kauniainen:   6f0458d4-42a3-434a-b9be-20c19fcfa5c3
        # vantaa:       6d78f89c-9fd7-41d9-84e0-4b78c0fa25ce

        username = options['username']
        password = options['password']

        if options['city'] == 'espoo':
            city = '520a4492-cb78-498b-9c82-86504de88dce'
        elif options['city'] == 'helsinki':
            city = '83e74666-0836-4c1d-948a-4b34a8b90301'
        elif options['city'] == 'kauniainen':
            city = '6f0458d4-42a3-434a-b9be-20c19fcfa5c3'
        elif options['city'] == 'vantaa':
            city = '6d78f89c-9fd7-41d9-84e0-4b78c0fa25ce'
        else:
            city = options['city']

        department = Department.objects.get(uuid=city)

        if department is not None:
            user = User.objects.filter(username=username)
            if len(user) == 0:
                user = User.objects.create_user(username, password=password)
                user.is_superuser = True
                user.is_staff = True
                user.save()

                userorganization = UserOrganization()
                userorganization.user = user
                userorganization.organization = department
                userorganization.save()
                self.stdout.write('User {} created'.format(username))
            else:
                self.stdout.write('User {} already exists'.format(username))

        else:
            self.stdout.write('City {} not found'.format(city))
