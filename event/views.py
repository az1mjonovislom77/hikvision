from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from event.models import AccessEvent
from event.serializers import AccessEventSerializer
from event.services.event_sync import EventSyncService
from person.models import Employee
from rest_framework.permissions import IsAuthenticated

from utils.models import Devices


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = None


class AccessEventList(ListAPIView):
    serializer_class = AccessEventSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        EventSyncService.sync_events()
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return EventSyncService.get_events_queryset()
        user_devices = Devices.objects.filter(user=user)
        employees = Employee.objects.filter(device__in=user_devices)
        if not employees.exists():
            return AccessEvent.objects.none()

        return EventSyncService.get_events_queryset().filter(employee__in=employees)
