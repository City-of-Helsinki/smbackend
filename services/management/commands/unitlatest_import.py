from django.core.management.base import BaseCommand
from observations.models import Observation, ObservableProperty, UnitLatestObservation
from services.models import Unit


class Command(BaseCommand):

    def handle(self, **options):

        for unit in Unit.objects.all():

            obs = Observation.objects.filter(unit=unit)

            if not obs:
                continue

            obs_values = obs.values('id', 'time', 'property')[0]
            obs = obs.latest('time')
            try:
                unit_latest = UnitLatestObservation.objects.create(observation=obs,
                                                         property=ObservableProperty.objects.get(id=obs_values['property']),
                                                         unit=unit)
            except Exception as e:
                print(e)
                continue
