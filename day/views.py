from day.models import DayOff, WorkDay, Shift, BreakTime
from day.serializers.serializers import DayOffCreateSerializer, DayOffGetSerializer, WorkDayCreateSerializer, \
    WorkDayGetSerializer, ShiftCreateSerializer, ShiftGetSerializer, BreakTimeCreateSerializer, BreakTimeGetSerializer
from utils.schema import user_extend_schema
from utils.views.base import BaseUserViewSet


@user_extend_schema("DayOff")
class DayOffViewSet(BaseUserViewSet):
    queryset = DayOff.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return DayOffCreateSerializer
        return DayOffGetSerializer


@user_extend_schema("WorkDay")
class WorkDayViewSet(BaseUserViewSet):
    queryset = WorkDay.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return WorkDayCreateSerializer
        return WorkDayGetSerializer


@user_extend_schema("Shift")
class ShiftViewSet(BaseUserViewSet):
    queryset = Shift.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ShiftCreateSerializer
        return ShiftGetSerializer


@user_extend_schema("BreakTime")
class BreakTimeViewSet(BaseUserViewSet):
    queryset = BreakTime.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BreakTimeCreateSerializer
        return BreakTimeGetSerializer
