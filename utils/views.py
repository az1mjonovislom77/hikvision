from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from .models import Devices, Department, Branch
from .serializers import DevicesSerializer, DepartmentSerializer, BranchSerializer
from rest_framework.permissions import IsAuthenticated


class PartialPutMixin:
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


@extend_schema(tags=['Devices'])
class DevicesViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Devices.objects.all()
    serializer_class = DevicesSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None


@extend_schema(tags=['Department'])
class DepartmentViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None


@extend_schema(tags=['Branch'])
class BranchViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None
