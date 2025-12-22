from drf_spectacular.utils import extend_schema, OpenApiParameter
from utils.models import Devices, Department, Branch, TelegramChannel
from utils.serializers import DevicesSerializer, DepartmentSerializer, BranchSerializer, TelegramChannelSerializer
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
    serializer_class = DepartmentSerializer


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
    serializer_class = BranchSerializer


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
