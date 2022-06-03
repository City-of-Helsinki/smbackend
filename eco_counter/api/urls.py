from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "eco_counter"

router = routers.DefaultRouter()
router.register("stations", views.StationViewSet, basename="stations")

router.register("hour_data", views.HourDataViewSet, basename="hour_data")
router.register("day_data", views.DayDataViewSet, basename="day_data")
router.register("week_data", views.WeekDataViewSet, basename="week_data")
router.register("month_data", views.MonthDataViewSet, basename="month_data")
router.register("year_data", views.YearDataViewSet, basename="year_data")

router.register("days", views.DayViewSet, basename="days")
router.register("weeks", views.WeekViewSet, basename="weeks")
router.register("months", views.MonthViewSet, basename="months")
router.register("years", views.YearViewSet, basename="years")

urlpatterns = [
    path("", include(router.urls), name="eco-counter"),
]
