from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "environment_data"


router = routers.DefaultRouter()

router.register("data", views.DataViewSet, basename="data")
router.register("stations", views.StationViewSet, basename="stations")
router.register("parameters", views.ParameterViewSet, basename="parameters")

urlpatterns = [
    path("api/v1/", include(router.urls), name="environment_data"),
]
