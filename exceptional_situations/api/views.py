import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
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


class SituationFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(method="filter_is_active")
    situation_type_str = django_filters.CharFilter(method="filter_situation_type_str")
    start_time__gt = django_filters.DateTimeFilter(method="filter_start_time__gt")
    start_time__lt = django_filters.DateTimeFilter(method="filter_start_time__lt")
    end_time__gt = django_filters.DateTimeFilter(method="filter_end_time__gt")
    end_time__lt = django_filters.DateTimeFilter(method="filter_end_time__lt")
    municipalities = django_filters.CharFilter(method="filter_municipalities")

    class Meta:
        model = Situation
        fields = {
            "situation_type": ["exact"],
            "situation_id": ["exact"],
            "release_time": ["lt", "gt"],
        }

    def filter_situation_type_str(self, queryset, fields, situation_type_str):
        ids = [
            obj.id for obj in queryset if obj.situation_type_str == situation_type_str
        ]
        return queryset.filter(id__in=ids)

    def filter_is_active(self, queryset, fields, active):
        ids = [obj.id for obj in queryset if obj.is_active == bool(active)]
        return queryset.filter(id__in=ids)

    def filter_start_time__gt(self, queryset, fields, start_time):
        ids = [obj.id for obj in queryset if obj.start_time > start_time]
        return queryset.filter(id__in=ids)

    def filter_start_time__lt(self, queryset, fields, start_time):
        ids = [obj.id for obj in queryset if obj.start_time < start_time]
        return queryset.filter(id__in=ids)

    def filter_end_time__gt(self, queryset, fields, end_time):
        ids = [obj.id for obj in queryset if obj.end_time > end_time]
        return queryset.filter(id__in=ids)

    def filter_end_time__lt(self, queryset, fields, end_time):
        ids = [obj.id for obj in queryset if obj.end_time < end_time]
        return queryset.filter(id__in=ids)

    def filter_municipalities(self, queryset, fields, municipalities):
        municipalities = municipalities.split(",")
        query = Q()
        for municiaplity in municipalities:
            query |= Q(announcements__municipalities__id__iexact=municiaplity.strip())
        return queryset.filter(query).distinct()


class SituationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Situation.objects.all()
    serializer_class = SituationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SituationFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


class SituationLocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SituationLocation.objects.all()
    serializer_class = SituationLocationSerializer


class SituationAnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SituationAnnouncement.objects.all()
    serializer_class = SituationAnnouncementSerializer


class SituationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SituationType.objects.all()
    serializer_class = SituationTypeSerializer
