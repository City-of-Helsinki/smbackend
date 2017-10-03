from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^tp(?P<unit_id>[0-9]+)/?$', views.unit_short_url, name='shortcutter-unit-url'),
]
