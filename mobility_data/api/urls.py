from django.urls import path, include
from rest_framework import routers
from . import views

app_name = "mobility_data"

router = routers.DefaultRouter()
router.register("group_types", views.GroupTypeViewSet, basename="group_types")
router.register("content_types", views.ContentTypeViewSet, basename="content_types")
router.register("mobile_units", views.MobileUnitViewSet, basename="mobile_units")
router.register("mobile_unit_groups", views.MobileUnitGroupViewSet, basename="mobile_unit_groups")

urlpatterns = [
    path("", include(router.urls), name="mobility_data"),
]