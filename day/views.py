from day.models import DayOff, WorkDay, Shift, BreakTime
from day.serializers.serializers import DayOffCreateSerializer, DayOffGetSerializer, WorkDayCreateSerializer, \
    WorkDayGetSerializer, ShiftCreateSerializer, ShiftGetSerializer, BreakTimeCreateSerializer, BreakTimeGetSerializer
from utils.base.views_base import BaseUserViewSet, ReadWriteSerializerMixin
from utils.utils.schema import user_extend_schema


@user_extend_schema("DayOff")
class DayOffViewSet(ReadWriteSerializerMixin, BaseUserViewSet):
    queryset = DayOff.objects.all()
    write_serializer = DayOffCreateSerializer
    read_serializer = DayOffGetSerializer


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
