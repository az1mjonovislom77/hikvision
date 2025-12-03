from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from person.models import Staff
from person.serializers import StaffSerializer
from utils.views import PartialPutMixin
from rest_framework.permissions import IsAuthenticated


@extend_schema(tags=['Staff'])
class StaffViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None
