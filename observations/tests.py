import datetime as dt
from django.test import TestCase
from services.models import OntologyWord, Unit
from observations.models import *
import pytz

EXAMPLE_TIMESTAMPS = [
    dt.datetime(year=2015, month=12, day=24, hour=12, minute=1, second=12, tzinfo=pytz.utc),
    dt.datetime(year=2016, month=12, day=24, hour=12, minute=1, second=12, tzinfo=pytz.utc)
]

class ContinuousObservationTestCase(TestCase):

    def setUp(self):
        skiing_service = OntologyWord.objects.create(
            id=1,
            name='Skiing track',
            unit_count=0,
            last_modified_time=EXAMPLE_TIMESTAMPS[0])
        example_track = Unit.objects.create(
            id=1,
            name='Herttoniemi 5 km',
            provider_type=1,
            organization_id=1,
            origin_last_modified_time=EXAMPLE_TIMESTAMPS[0])
        example_track.services.add(skiing_service)
        thickness = ObservableProperty.objects.create(
            name='Snow thickness',
            measurement_unit='cm')
        thickness.services.add(skiing_service)

    def test_valid_observation_can_be_made(self):
        ContinuousObservation.objects.create(
            property=ObservableProperty.objects.get(name='Snow thickness'),
            timestamp=EXAMPLE_TIMESTAMPS[1],
            unit=Unit.objects.get(name='Herttoniemi 5 km'),
            value=2.45)
