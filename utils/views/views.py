from drf_spectacular.utils import extend_schema
from utils.models import Devices, Department, Branch
from utils.serializers import DevicesSerializer, DepartmentSerializer, BranchSerializer
from utils.views.base import BaseUserViewSet


@extend_schema(tags=['Devices'])
class DevicesViewSet(BaseUserViewSet):
    queryset = Devices.objects.all()
    serializer_class = DevicesSerializer


@extend_schema(tags=['Department'])
class DepartmentViewSet(BaseUserViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


@extend_schema(tags=['Branch'])
class BranchViewSet(BaseUserViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
