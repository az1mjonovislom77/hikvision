from day.api.serializers import (
    BreakTimeCreateSerializer,
    BreakTimeGetSerializer,
    DayOffCreateSerializer,
    DayOffGetSerializer,
    ShiftCreateSerializer,
    ShiftGetSerializer,
    WorkDayCreateSerializer,
    WorkDayGetSerializer,
)
from day.selectors.day import break_time_queryset, day_off_queryset, shift_queryset, work_day_queryset
from utils.base.views_base import BaseUserViewSet, ReadWriteSerializerMixin
from utils.utils.schema import user_extend_schema


@user_extend_schema("DayOff")
class DayOffViewSet(ReadWriteSerializerMixin, BaseUserViewSet):
    queryset = day_off_queryset()
    write_serializer = DayOffCreateSerializer
    read_serializer = DayOffGetSerializer


@user_extend_schema("WorkDay")
class WorkDayViewSet(BaseUserViewSet):
    queryset = work_day_queryset()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return WorkDayCreateSerializer
        return WorkDayGetSerializer


@user_extend_schema("Shift")
class ShiftViewSet(BaseUserViewSet):
    queryset = shift_queryset()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ShiftCreateSerializer
        return ShiftGetSerializer


@user_extend_schema("BreakTime")
class BreakTimeViewSet(BaseUserViewSet):
    queryset = break_time_queryset()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BreakTimeCreateSerializer
        return BreakTimeGetSerializer
