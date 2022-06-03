from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "bicycle_network"

router = routers.DefaultRouter()
router.register(
    "bicycle_networks", views.BicycleNetworkViewSet, basename="bicycle_networks"
)
router.register(
    "bicycle_networkparts",
    views.BicycleNetworkPartViewSet,
    basename="bicycle_networkparts",
)

urlpatterns = [
    path("", include(router.urls), name="bicycle_network"),
]
