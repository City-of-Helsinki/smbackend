from django.urls import include, path
from rest_framework import routers

from exceptional_situations.api import views

app_name = "exceptional_stituations"


router = routers.DefaultRouter()

router.register("situation", views.SituationViewSet, basename="situation")
router.register("situation_type", views.SituationTypeViewSet, basename="situation_type")
router.register(
    "situation_location", views.SituationLocationViewSet, basename="situation_location"
)
router.register(
    "situation_announcement",
    views.SituationAnnouncementViewSet,
    basename="situation_announcement",
)

urlpatterns = [
    path("api/v1/", include(router.urls), name="exceptional_stituations"),
]
