from event.services.event_sync import EventSyncService
from user.models import User
from utils.models import Devices
from event.models import AccessEvent
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.generics import ListAPIView
from event.serializers import AccessEventSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = None


def _truthy_param(val):
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("1", "true", "yes", "on")


@extend_schema(
    tags=["Event"],
    parameters=[
        OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun"),
        OpenApiParameter(
            name="full",
            type=bool,
            required=False,
            description=(
                    "True bo‘lsa qurilmadagi event bufferidan to‘liq yuklaydi (eski yozuvlar ham). "
                    "Standart: false. full=true yuborilsa qurilmadagi eski eventlar ham olinadi."
            ),
        ),
    ],
)
class EventSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
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

        full_param = request.query_params.get("full")
        if full_param is None and isinstance(getattr(request, "data", None), dict):
            full_param = request.data.get("full")

        full = False if full_param is None else _truthy_param(full_param)

        total_saved = EventSyncService.sync_events(devices, full=full)

        return Response(
            {
                "success": True,
                "added": total_saved,
                "deleted": 0,
                "full": full,
            },
            status=200,
        )


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
        return qs.filter(device__in=devices)
