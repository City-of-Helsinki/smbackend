import re

from django.conf import settings
from rest_framework.pagination import PageNumberPagination

KML_REGEXP = re.compile(settings.KML_REGEXP)


class Pagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_page_size(self, request):
        if hasattr(request, "accepted_media_type") and re.match(
            KML_REGEXP, request.accepted_media_type
        ):
            return 30000
        return super().get_page_size(request)
