from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from event.models import AccessEvent
from event.serializers import AccessEventSerializer
from event.services.event_state import get_last_event_time, set_last_event_time
from event.services.event_sync import EventSyncService
from event.utils.fetch import fetch_face_events
from person.models import Employee
from user.models import User
from utils.models import Devices
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from utils.telegram import send_telegram


class CustomPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = None


@extend_schema(
    tags=["Event"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun. Qaysi user device eventlari sync qilinadi."
        )
    ]
)
class EventSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.is_superuser or user.is_staff:
            user_id = request.query_params.get("user_id")
            if not user_id:
                return Response({"error": "user_id majburiy"}, status=400)

            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                return Response({"error": "User topilmadi"}, status=404)

            devices = Devices.objects.filter(user=target_user)
        else:
            devices = Devices.objects.filter(user=user)

        if not devices.exists():
            return Response({"error": "Device topilmadi"}, status=400)

        added = EventSyncService.sync_events(devices)

        return Response({"success": True, "added": added})


@extend_schema(tags=["Event"])
class AccessEventListView(ListAPIView):
    serializer_class = AccessEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = AccessEvent.objects.select_related("device", "employee")

        if user.is_superuser or user.is_staff:
            return qs

        devices = Devices.objects.filter(user=user)
        employees = Employee.objects.filter(device__in=devices)

        return qs.filter(employee__in=employees)


class RealTimeEventToTelegramAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        last_time = get_last_event_time()

        try:
            new_count = fetch_face_events(since=last_time)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=500)

        if new_count:
            set_last_event_time(timezone.now())
            send_telegram(f"🚨 {new_count} ta YANGI EVENT aniqlandi")

        return Response({"success": True, "new_events": new_count})
