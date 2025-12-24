from day.models import DayOff, WorkDay, Shift, BreakTime
from day.serializers.serializers import DayOffCreateSerializer, DayOffGetSerializer, WorkDayCreateSerializer, \
    WorkDayGetSerializer, ShiftCreateSerializer, ShiftGetSerializer, BreakTimeCreateSerializer, BreakTimeGetSerializer
from utils.schema import user_extend_schema
from utils.views.base import BaseUserViewSet


@user_extend_schema("DayOff")
class DayOffViewSet(BaseUserViewSet):
    queryset = DayOff.objects.all()
    create_serializer_class = DayOffCreateSerializer
    retrieve_serializer_class = DayOffGetSerializer


@user_extend_schema("WorkDay")
class WorkDayViewSet(BaseUserViewSet):
    queryset = WorkDay.objects.all()
    create_serializer_class = WorkDayCreateSerializer
    retrieve_serializer_class = WorkDayGetSerializer


@user_extend_schema("Shift")
class ShiftViewSet(BaseUserViewSet):
    queryset = Shift.objects.all()
    create_serializer_class = ShiftCreateSerializer
    retrieve_serializer_class = ShiftGetSerializer


@user_extend_schema("BreakTime")
class BreakTimeViewSet(BaseUserViewSet):
    queryset = BreakTime.objects.all()
    create_serializer_class = BreakTimeCreateSerializer
    retrieve_serializer_class = BreakTimeGetSerializer
