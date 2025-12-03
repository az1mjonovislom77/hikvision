from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from day.models import DayOff, WorkDay, Shift, BreakTime
from day.serializers import DayOffSerializer, WorkDaySerializer, ShiftSerializer, BreakTimeSerializer
from utils.views import PartialPutMixin


@extend_schema(tags=['DayOff'])
class DayOffViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = DayOff.objects.all()
    serializer_class = DayOffSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None


@extend_schema(tags=['WorkDay'])
class WorkDayViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = WorkDay.objects.all()
    serializer_class = WorkDaySerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None


@extend_schema(tags=['Shift'])
class ShiftViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None


@extend_schema(tags=['BreakTime'])
class BreakTimeViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = BreakTime.objects.all()
    serializer_class = BreakTimeSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None
