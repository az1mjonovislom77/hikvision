from drf_spectacular.utils import extend_schema, OpenApiParameter
from day.models import DayOff, WorkDay, Shift, BreakTime
from day.serializers import DayOffSerializer, WorkDaySerializer, ShiftSerializer, BreakTimeSerializer
from utils.views.base import BaseUserViewSet


@extend_schema(
    tags=["DayOff"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class DayOffViewSet(BaseUserViewSet):
    queryset = DayOff.objects.all()
    serializer_class = DayOffSerializer


@extend_schema(
    tags=["WorkDay"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class WorkDayViewSet(BaseUserViewSet):
    queryset = WorkDay.objects.all()
    serializer_class = WorkDaySerializer


@extend_schema(
    tags=["Shift"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class ShiftViewSet(BaseUserViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer


@extend_schema(
    tags=["BreakTime"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class BreakTimeViewSet(BaseUserViewSet):
    queryset = BreakTime.objects.all()
    serializer_class = BreakTimeSerializer
