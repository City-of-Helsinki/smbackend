from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "street_maintenance"

router = routers.DefaultRouter()
router.register("active_events", views.ActiveEventsViewSet, basename="active_events")

router.register(
    "maintenance_works", views.MaintenanceWorkViewSet, basename="maintenance_works"
)
router.register(
    "maintenance_units", views.MaintenanceUnitViewSet, basename="maintenance_units"
)

router.register(
    "geometry_history", views.GeometryHitoryViewSet, basename="geometry_history"
)

urlpatterns = [
    # re_path("^street_maintenance/active_events", )
    path("", include(router.urls), name="street_maintenance"),
]
