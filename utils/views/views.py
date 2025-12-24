from utils.models import Devices, Department, Branch, TelegramChannel, Subscription, Plan
from utils.schema import user_extend_schema
from utils.serializers import DevicesSerializer, TelegramChannelSerializer, \
    BranchGetSerializer, BranchCreateSerializer, DepartmentCreateSerializer, DepartmentGetSerializer, \
    PlanSerializer, SubscriptionCreateSerializer, SubscriptionDetailSerializer
from utils.views.base import BaseUserViewSet, User
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


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
    create_serializer_class = SubscriptionCreateSerializer
    retrieve_serializer_class = SubscriptionDetailSerializer

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
