from rest_framework import serializers

from exceptional_situations.models import (
    Situation,
    SituationAnnouncement,
    SituationLocation,
    SituationType,
)


class SituationLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationLocation
        fields = ["id", "location", "geometry", "details"]


class SituationAnnouncementSerializer(serializers.ModelSerializer):
    location = SituationLocationSerializer()
    municipalities = serializers.SerializerMethodField()

    class Meta:
        model = SituationAnnouncement
        fields = [
            "id",
            "title",
            "description",
            "start_time",
            "end_time",
            "additional_info",
            "location",
            "municipalities",
        ]

    def get_municipalities(self, obj):
        return [m.id for m in obj.municipalities.all()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SituationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationType
        fields = "__all__"


class SituationSerializer(serializers.ModelSerializer):
    announcements = SituationAnnouncementSerializer(many=True, read_only=True)

    class Meta:
        model = Situation
        fields = [
            "id",
            "is_active",
            "start_time",
            "end_time",
            "situation_id",
            "release_time",
            "situation_type",
            "situation_type_str",
            "situation_sub_type_str",
            "announcements",
        ]
