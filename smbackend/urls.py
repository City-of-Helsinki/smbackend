from django.conf.urls import patterns, include, url
from tastypie.api import Api
from services.api import all_resources

# from django.contrib import admin
# admin.autodiscover()

v1_api = Api(api_name='v1')
for res in all_resources:
    v1_api.register(res())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'smbackend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^', include(v1_api.urls)),
    # url(r'^admin/', include(admin.site.urls)),
)
