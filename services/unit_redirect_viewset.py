from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from urllib.parse import parse_qs
from services.models.service_mapping import ServiceMapping
from django.http import QueryDict


class UnitRedirectViewSet(viewsets.ViewSet):
    """
    Implement redirecting from old TPR v3 service id
    based filters in unit endpoint to new TPR v4 ontologytree node ids.

    """
    def _malformed_error(self):
        return Response({'error': 'malformed service id'}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request):
        params = self.request.query_params.copy()
        service_id_param = None
        try:
            service_id_param = params.pop('service')
        except KeyError:
            return self._malformed_error()
        if not service_id_param or len(service_id_param) == 0:
            return self._malformed_error()
        try:
            service_ids = [str(int(s)) for s in service_id_param[0].split(",")]
        except ValueError:
            return self._malformed_error()
        queryset = ServiceMapping.objects.filter(service_id__in=service_ids)
        if queryset.count() == 0:
            return Response({'message': 'service id not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self._generate_redirect_parameters(queryset, params))

    def _generate_redirect_parameters(self, queryset, params):
        for mapping in queryset:
            params.appendlist('service_node', str(mapping.node_id.id))
            additional_filter = parse_qs(mapping.filter)
            for k, val in additional_filter.items():
                for x in val:
                    params.appendlist(k, x)

        final_query = QueryDict().copy()
        for key, val in params.lists():
            final_query[key] = ','.join(val)

        return final_query
