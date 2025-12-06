from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from event.serializers import AccessEventSerializer
from event.services.event_sync import EventSyncService
from person.models import Employee
from utils.models import Devices
from rest_framework.permissions import IsAuthenticated


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
        queryset = EventSyncService.get_events_queryset()
        if user.is_superuser or user.is_staff:
            return queryset
        user_devices = Devices.objects.filter(user=user)
        employees = Employee.objects.filter(device__in=user_devices)
        if not employees.exists():
            return queryset.none()
        return queryset.filter(employee__in=employees)
