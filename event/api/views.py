import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from event.api.serializers import AccessEventSerializer
from event.selectors.events import get_access_events_queryset, get_user_devices
from event.services.api import EventSyncAPIService, truthy_param

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = None


@extend_schema(
    tags=["Event"],
    parameters=[
        OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun"),
        OpenApiParameter(name="full", type=bool, required=False),
    ],
)
class EventSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        logger.info(
            "event sync request started: user_id=%s role=%s is_staff=%s query_params=%s body_keys=%s",
            user.id,
            getattr(user, "role", None),
            user.is_staff,
            dict(request.query_params),
            sorted(request.data.keys()) if isinstance(getattr(request, "data", None), dict) else [],
        )

        devices, error, status_code = EventSyncAPIService.resolve_devices(
            user=user,
            user_id=request.query_params.get("user_id"),
        )
        if error:
            return Response(error, status=status_code)

        if not devices.exists():
            logger.warning("event sync aborted: no devices found for user_id=%s", user.id)
            return Response({"error": "Device topilmadi"}, status=400)

        full_param = request.query_params.get("full")
        if full_param is None and isinstance(getattr(request, "data", None), dict):
            full_param = request.data.get("full")

        full = False if full_param is None else truthy_param(full_param)

        return Response(EventSyncAPIService.sync(user=user, devices=devices, full=full), status=200)


@extend_schema(tags=["Event"])
class AccessEventListView(ListAPIView):
    serializer_class = AccessEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = get_access_events_queryset()

        if user.is_superuser or user.is_staff:
            return qs

        devices = get_user_devices(user=user)
        return qs.filter(device__in=devices)
