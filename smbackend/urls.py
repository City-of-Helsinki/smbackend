from django.conf.urls import patterns, include, url
from services.api import all_views as services_views
from rest_framework import routers
from munigeo.api import all_views as munigeo_views

# from django.contrib import admin
# admin.autodiscover()

router = routers.DefaultRouter()
for view in services_views + munigeo_views:
    kwargs = {}
    if 'base_name' in view:
        kwargs['base_name'] = view['base_name']
    router.register(view['name'], view['class'], **kwargs)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'smbackend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^', include(v1_api.urls)),
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/', include(router.urls))
)
