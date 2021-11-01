from rest_framework import serializers
from ...models import (
    GroupType,
)

class GroupTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupType
        fields = [
            "id", 
            "type_name",
            "description"
            ]