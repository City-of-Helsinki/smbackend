from rest_framework import viewsets

from exceptional_situations.api.serializers import (
    SituationAnnouncementSerializer,
    SituationLocationSerializer,
    SituationSerializer,
    SituationTypeSerializer,
)
from exceptional_situations.models import (
    Situation,
    SituationAnnouncement,
    SituationLocation,
    SituationType,
)


class SituationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Situation.objects.all()
    serializer_class = SituationSerializer


class SituationLocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SituationLocation.objects.all()
    serializer_class = SituationLocationSerializer


class SituationAnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SituationAnnouncement.objects.all()
    serializer_class = SituationAnnouncementSerializer


class SituationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SituationType.objects.all()
    serializer_class = SituationTypeSerializer
