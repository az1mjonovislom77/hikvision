from django.urls import include, path
from rest_framework.routers import DefaultRouter

from day.api.views import BreakTimeViewSet, DayOffViewSet, ShiftViewSet, WorkDayViewSet

router = DefaultRouter()
router.register("day_off", DayOffViewSet)
router.register("work_day", WorkDayViewSet)
router.register("shift", ShiftViewSet)
router.register("break_time", BreakTimeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
