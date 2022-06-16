from rest_framework import serializers

from ...models import ContentType


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ["id", "name", "type_name", "description"]
