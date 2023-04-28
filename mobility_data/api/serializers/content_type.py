from rest_framework import serializers

from ...models import ContentType


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = [
            "id",
            "type_name",
            "name",
            "name_sv",
            "name_en",
            "description",
            "description_sv",
            "description_en",
        ]
