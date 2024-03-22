from rest_framework import serializers

from exceptional_situations.models import (
    Situation,
    SituationAnnouncement,
    SituationLocation,
    SituationType,
)


class SituationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Situation
        fields = [
            "id",
            "is_active",
            "situation_id",
            "release_time",
            "situation_type",
            "situation_type_str",
            "situation_sub_type_str",
        ]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["locations"] = SituationLocationSerializer(
            obj.locations, many=True
        ).data
        representation["announcements"] = SituationAnnouncementSerializer(
            obj.announcements, many=True
        ).data
        return representation


class SituationAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationAnnouncement
        fields = "__all__"


class SituationLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationLocation
        fields = "__all__"


class SituationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SituationType
        fields = "__all__"
