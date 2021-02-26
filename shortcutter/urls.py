from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r"^tp(?P<unit_id>[0-9]+)/?$", views.unit_short_url, name="shortcutter-unit-url"
    ),
]
