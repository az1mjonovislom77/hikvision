from utils.models import Devices, Department, Branch, TelegramChannel, Subscription, Plan, Notification
from utils.utils.schema import user_extend_schema
from utils.serializers import DevicesSerializer, TelegramChannelSerializer, \
    BranchGetSerializer, BranchCreateSerializer, DepartmentCreateSerializer, DepartmentGetSerializer, \
    PlanSerializer, SubscriptionCreateSerializer, SubscriptionDetailSerializer, NotificationSerializer, \
    AdminNotificationSerializer
from utils.views.base import BaseUserViewSet, User
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated


@user_extend_schema("Devices")
class DevicesViewSet(BaseUserViewSet):
    queryset = Devices.objects.all()
    serializer_class = DevicesSerializer


@user_extend_schema("Department")
class DepartmentViewSet(BaseUserViewSet):
    queryset = Department.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DepartmentCreateSerializer
        return DepartmentGetSerializer


@user_extend_schema("Branch")
class BranchViewSet(BaseUserViewSet):
    queryset = Branch.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BranchCreateSerializer
        return BranchGetSerializer


@user_extend_schema("TelegramChannel")
class TelegramChannelViewSet(BaseUserViewSet):
    queryset = TelegramChannel.objects.all()
    serializer_class = TelegramChannelSerializer


@extend_schema(tags=["Plan"])
class PlanViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "delete"]
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
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
        self.perform_create(serializer)
        response_serializer = self.retrieve_serializer_class(serializer.instance, context=self.get_serializer_context())

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        request_user = self.request.user

        if request_user.is_staff or request_user.role == request_user.UserRoles.SUPERADMIN:
            user_id = self.request.query_params.get("user_id")
            target_user = User.objects.get(id=user_id)
        else:
            target_user = request_user

        plan = serializer.validated_data["plan"]
        Subscription.objects.filter(user=target_user, is_active=True).update(is_active=False)
        start_date = timezone.now()
        end_date = start_date + relativedelta(months=plan.duration_months)
        serializer.save(user=target_user, start_date=start_date, end_date=end_date, is_active=True, is_paid=True)


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
        user_ids = request.data.get("user_ids")
        text = request.data.get("text")

        if not text:
            return Response({"text": "Majburiy"}, status=400)

        if user_ids:
            users = User.objects.filter(id__in=user_ids)
        else:
            users = User.objects.all()

        Notification.objects.bulk_create([Notification(user=u, text=text) for u in users])

        return Response({"detail": "Notification yuborildi"}, status=201)
