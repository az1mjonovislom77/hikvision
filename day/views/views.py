from drf_spectacular.utils import extend_schema
from day.models import DayOff, WorkDay, Shift, BreakTime
from day.serializers import DayOffSerializer, WorkDaySerializer, ShiftSerializer, BreakTimeSerializer
from day.views.base import BaseUserModelViewSet


@extend_schema(tags=['DayOff'])
class DayOffViewSet(BaseUserModelViewSet):
    queryset = DayOff.objects.all()
    serializer_class = DayOffSerializer


@extend_schema(tags=['WorkDay'])
class WorkDayViewSet(BaseUserModelViewSet):
    queryset = WorkDay.objects.all()
    serializer_class = WorkDaySerializer


@extend_schema(tags=['Shift'])
class ShiftViewSet(BaseUserModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer


@extend_schema(tags=['BreakTime'])
class BreakTimeViewSet(BaseUserModelViewSet):
    queryset = BreakTime.objects.all()
    serializer_class = BreakTimeSerializer
