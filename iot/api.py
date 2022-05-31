import logging

from django.core.cache import cache
from django.db import connection, reset_queries
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView

from iot.models import IoTData
from iot.utils import get_cache_keys, get_source_names

logger = logging.getLogger("iot")


class IotDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = IoTData
        fields = "__all__"


class IoTViewSet(GenericAPIView):
    queryset = IoTData.objects.all()

    def get(self, request):
        params = self.request.query_params
        source_name = params.get("source_name", None)
        source_names = get_source_names()

        if not source_name:
            raise NotFound(
                f"'source_name' param not found, source_name arguments are: {source_names}"
            )
        if source_name not in source_names:
            raise NotFound(
                f"'source_name' {source_name} not found. Choices are: {source_names}"
            )

        key_queryset, key_serializer = get_cache_keys(source_name)
        cached_data = cache.get_many([key_queryset, key_serializer])
        if not cached_data:
            queryset = IoTData.objects.filter(data_source__source_name=source_name)
            serializer = IotDataSerializer(queryset, many=True)
            # Set timeout to None(never expire), cache is cleared during import.
            cache.set_many(
                {key_serializer: serializer, key_queryset: queryset}, timeout=None
            )
        else:
            queryset = cached_data[key_queryset]
            serializer = cached_data[key_serializer]

        if logger.level <= logging.DEBUG:
            logger.debug(connection.queries)
            queries_time = sum([float(s["time"]) for s in connection.queries])
            if connection.queries:
                num_queries = len(connection.queries)
            else:
                num_queries = 0
            logger.debug(
                f"IoT queries total execution time: {queries_time} Num queries: {num_queries}"
            )
            reset_queries()

        return self.get_paginated_response(serializer.data)
