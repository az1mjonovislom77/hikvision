from drf_spectacular.utils import extend_schema
from utils.models import Devices, Department, Branch, TelegramChannel
from utils.serializers import DevicesSerializer, DepartmentSerializer, BranchSerializer, TelegramChannelSerializer
from utils.views.base import BaseUserViewSet


@extend_schema(tags=['Devices'])
class DevicesViewSet(BaseUserViewSet):
    queryset = Devices.objects.all()
    serializer_class = DevicesSerializer
    http_method_names = ["get", "post", "put", "delete"]


@extend_schema(tags=['Department'])
class DepartmentViewSet(BaseUserViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    http_method_names = ["get", "post", "put", "delete"]


@extend_schema(tags=['Branch'])
class BranchViewSet(BaseUserViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    http_method_names = ["get", "post", "put", "delete"]


@extend_schema(tags=['TelegramChannel'])
class TelegramChannelViewSet(BaseUserViewSet):
    queryset = TelegramChannel.objects.all()
    serializer_class = TelegramChannelSerializer
    http_method_names = ["get", "post", "put", "delete"]
