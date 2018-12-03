from django.core.management.base import BaseCommand
from observations.models import Observation, ObservableProperty, UnitLatestObservation
from services.models import Unit


class Command(BaseCommand):
    count = 0

    def handle(self, **options):
        UnitLatestObservation.objects.all().delete()

        for unit in Unit.objects.all():
            self.insert(unit)

    def insert(self, unit):

        for oprperty in ObservableProperty.objects.all():
            obs = Observation.objects.filter(unit=unit, property=oprperty)
            if not obs:
                continue

            obs = obs.latest('time')

            try:
                UnitLatestObservation.objects.create(observation=obs, property=oprperty, unit=unit)
                self.count = self.count + 1
            except Exception as e:
                print(e)
                continue
