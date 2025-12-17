from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from event.serializers import AccessEventSerializer
from event.services.event_sync import EventSyncService
from person.models import Employee
from utils.models import Devices
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated


class CustomPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = None


@extend_schema(tags=["Event"])
class AccessEventList(ListAPIView):
    serializer_class = AccessEventSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        EventSyncService.sync_events()
        user = self.request.user
        queryset = EventSyncService.get_events_queryset()
        if user.UserRoles.SUPERADMIN or user.is_staff:
            return queryset
        user_devices = Devices.objects.filter(user=user)
        employees = Employee.objects.filter(device__in=user_devices)
        if not employees.exists():
            return queryset.none()
        return queryset.filter(employee__in=employees)


# class RealTimeEventToTelegramAPIView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         last_time = get_last_event_time()
#
#         try:
#             new_count = fetch_face_events(since=last_time)
#         except Exception as e:
#             return Response(
#                 {"success": False, "error": str(e)},
#                 status=500
#             )
#
#         if new_count:
#             set_last_event_time(timezone.now())
#             send_telegram(f"🚨 {new_count} ta YANGI EVENT aniqlandi")
#
#         return Response({
#             "success": True,
#             "new_events": new_count
#         })
