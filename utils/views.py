from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.services.smartcity_daily_stats import SmartCityDailyStatsService
from utils.services.smartcity_stats import SmartCityStatsService
from utils.utils.schema import user_extend_schema
from utils.services.subscription import SubscriptionService
from utils.services.notifications import NotificationService
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from utils.base.views_base import BaseUserViewSet, User, ReadWriteSerializerMixin
from utils.models import Devices, Department, Branch, TelegramChannel, Subscription, Plan, Notification
from utils.serializers import DevicesSerializer, TelegramChannelSerializer, \
    BranchGetSerializer, BranchCreateSerializer, DepartmentCreateSerializer, DepartmentGetSerializer, \
    PlanSerializer, SubscriptionCreateSerializer, SubscriptionDetailSerializer, NotificationSerializer, \
    AdminNotificationSerializer


@user_extend_schema("Devices")
class DevicesViewSet(BaseUserViewSet):
    queryset = Devices.objects.all()
    serializer_class = DevicesSerializer


@user_extend_schema("Department")
class DepartmentViewSet(ReadWriteSerializerMixin, BaseUserViewSet):
    queryset = Department.objects.all()
    write_serializer = DepartmentCreateSerializer
    read_serializer = DepartmentGetSerializer


@user_extend_schema("Branch")
class BranchViewSet(ReadWriteSerializerMixin, BaseUserViewSet):
    queryset = Branch.objects.all()
    write_serializer = BranchCreateSerializer
    read_serializer = BranchGetSerializer


@extend_schema(tags=['TelegramChannel'],
               parameters=[
                   OpenApiParameter(name="branch_id", type=int, required=True),
                   OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun")
               ])
class TelegramChannelViewSet(BaseUserViewSet):
    queryset = TelegramChannel.objects.all()
    serializer_class = TelegramChannelSerializer


@extend_schema(tags=["Plan"])
class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = None


@user_extend_schema("Subscription")
class SubscriptionViewSet(BaseUserViewSet):
    queryset = Subscription.objects.select_related("plan")

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return SubscriptionCreateSerializer
        return SubscriptionDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user = SubscriptionService.resolve_target_user(request.user, request.query_params.get("user_id"))
        plan = serializer.validated_data["plan"]
        subscription = SubscriptionService.create_subscription(serializer=serializer, user=target_user, plan=plan)
        response = SubscriptionDetailSerializer(subscription, context=self.get_serializer_context())

        return Response(response.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Notification"])
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    pagination_class = None

    def get_queryset(self):
        user = self.request.user

        if user.is_staff or user.role == User.UserRoles.SUPERADMIN:
            return self.queryset.select_related("user").order_by("-created_at")

        return self.queryset.filter(user=user).order_by("-created_at")


@extend_schema(tags=["Notification"])
class AdminNotificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminNotificationSerializer

    def create(self, request):
        text = request.data.get("text")
        user_ids = request.data.get("user_ids")

        if not text:
            return Response({"text": "Majburiy"}, status=status.HTTP_400_BAD_REQUEST)

        users = NotificationService.resolve_users(user_ids)
        NotificationService.send_bulk(text=text, users=users)

        return Response({"detail": "Notification yuborildi"}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["SmartCityStats"], parameters=[OpenApiParameter(name="timeFilter", type=str)])
class SmartCityAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        time_filter = request.GET.get("timeFilter", "week")

        try:
            service = SmartCityStatsService(time_filter)
            data = service.build()
        except ValueError:
            return Response({"success": False, "message": "Invalid timeFilter"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "success": True,
                "message": "Data fetched successfully",
                "data": data,
            }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["SmartCityDaily"],
    parameters=[
        OpenApiParameter(name="date", type=str, required=True),
        OpenApiParameter(name="mahalla", type=int, required=False),
    ]
)
class SmartCityDailyAPIView(APIView):

    def get(self, request):
        date = request.GET.get("date")
        mahalla = request.GET.get("mahalla")

        if not date:
            return Response({"success": False, "message": "date parameter is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        if mahalla is not None:
            try:
                mahalla = int(mahalla)
            except ValueError:
                return Response({"success": False, "message": "mahalla must be integer"},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            service = SmartCityDailyStatsService(date=date, mahalla_id=mahalla)
            data = service.build()

        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "success": True,
                "message": "Daily stats fetched successfully",
                "data": data
            }, status=status.HTTP_200_OK
        )
