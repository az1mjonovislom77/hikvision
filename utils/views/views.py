from drf_spectacular.utils import extend_schema, OpenApiParameter
from utils.models import Devices, Department, Branch, TelegramChannel
from utils.serializers import DevicesSerializer, TelegramChannelSerializer, \
    BranchGetSerializer, BranchCreateSerializer, DepartmentCreateSerializer, DepartmentGetSerializer
from utils.views.base import BaseUserViewSet


@extend_schema(
    tags=["Devices"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class DevicesViewSet(BaseUserViewSet):
    queryset = Devices.objects.all()
    serializer_class = DevicesSerializer


@extend_schema(
    tags=["Department"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class DepartmentViewSet(BaseUserViewSet):
    queryset = Department.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DepartmentCreateSerializer
        return DepartmentGetSerializer


@extend_schema(
    tags=["Branch"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class BranchViewSet(BaseUserViewSet):
    queryset = Branch.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BranchCreateSerializer
        return BranchGetSerializer


@extend_schema(
    tags=["TelegramChannel"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun"
        )
    ]
)
class TelegramChannelViewSet(BaseUserViewSet):
    queryset = TelegramChannel.objects.all()
    serializer_class = TelegramChannelSerializer
