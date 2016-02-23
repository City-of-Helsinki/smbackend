from rest_framework.pagination import PageNumberPagination
import re

KML_RE = re.compile('application/vnd.google-earth\.kml')

class Pagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_page_size(self, request):
        if hasattr(request, 'accepted_media_type') and re.match(KML_RE, request.accepted_media_type):
            return 30000
        return super(Pagination, self).get_page_size(request)
