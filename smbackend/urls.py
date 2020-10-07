from django.conf.urls import include, url
from django.contrib import admin
from munigeo.api import all_views as munigeo_views
from rest_framework import routers

from observations.api import views as observations_views
from observations.views import obtain_auth_token
from services import views
from services.api import all_views as services_views
from services.unit_redirect_viewset import UnitRedirectViewSet
from shortcutter import urls as shortcutter_urls

router = routers.DefaultRouter()

registered_api_views = set()

for view in services_views + munigeo_views + observations_views:
    kwargs = {}
    if view["name"] in registered_api_views:
        continue
    else:
        registered_api_views.add(view["name"])

    if "basename" in view:
        kwargs["basename"] = view["basename"]
    router.register(view["name"], view["class"], **kwargs)


urlpatterns = [
    # Examples:
    # url(r'^$', 'smbackend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    # url(r'^', include(v1_api.urls)),
    # url(r'^admin/', include(admin.site.urls)),
    url(r"^admin/", admin.site.urls),
    url(r"^open311/", views.post_service_request, name="services"),
    url(r"^v2/", include(router.urls)),
    url(r"^v2/api-token-auth/", obtain_auth_token, name="api-auth-token"),
    url(r"^v2/redirect/unit/", UnitRedirectViewSet.as_view({"get": "list"})),
    url(r"^v2/suggestion/", views.suggestion, name="suggestion"),
    url(r"", include(shortcutter_urls)),
]
