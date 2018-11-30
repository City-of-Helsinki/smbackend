from django.core.management.base import BaseCommand
from observations.models import Observation, ObservableProperty, UnitLatestObservation, CategoricalObservation
from services.models import Unit


class Command(BaseCommand):

    def handle(self, **options):
        UnitLatestObservation.objects.all().delete()

        for unit in Unit.objects.all():

            obs = Observation.objects.get(unit=unit)

            if not obs:
                continue

            #obs_values = obs.values('id', 'time', 'property')[0]
            #for o in obs.
            obs = obs.latest('time')
            try:
                # unit_latest = UnitLatestObservation.objects.create(observation=obs,
                #                                          property=ObservableProperty.objects.get(id=obs_values['property'],
                #                                          unit=unit))
                unit_latest = UnitLatestObservation.objects.create(observation=CategoricalObservation.objects.get(getattr(obs, 'id'),
                                                                   property=ObservableProperty.objects.get(
                                                                        id=getattr(obs, 'property'),
                                                                        unit=unit)))
            except Exception as e:
                print(e)
                continue
            print(unit_latest)
