from django.urls import path, include
from rest_framework.routers import DefaultRouter
from day.views import DayOffViewSet, WorkDayViewSet, ShiftViewSet, BreakTimeViewSet

router = DefaultRouter()
router.register('day_off', DayOffViewSet)
router.register('work_day', WorkDayViewSet)
router.register('shift', ShiftViewSet)
router.register('break_time', BreakTimeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
