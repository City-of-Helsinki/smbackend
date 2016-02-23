from rest_framework.pagination import PageNumberPagination
import re

KML_RE = re.compile('application/vnd.google-earth\.kml')

class Pagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_page_size(self, request):
        stored_size = self.max_page_size
        if hasattr(request, 'accepted_media_type') and re.match(KML_RE, request.accepted_media_type):
            self.max_page_size = 30000
        page_size = super(Pagination, self).get_page_size(request)
        self.max_page_size = stored_size
        return page_size
