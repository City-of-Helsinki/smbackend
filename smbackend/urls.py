from django.conf.urls import patterns, include, url
from tastypie.api import Api
from services.api import all_resources
from munigeo.api import all_resources as munigeo_resources
from rest_framework import routers

# from django.contrib import admin
# admin.autodiscover()

#v1_api = Api(api_name='v1')
#for res in all_resources:
    #v1_api.register(res())

#for res in munigeo_resources:
    #v1_api.register(res())

router = routers.DefaultRouter()
for res_name, view_set in all_resources.items():
    router.register(res_name, view_set)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'smbackend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^', include(v1_api.urls)),
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(router.urls))
)
