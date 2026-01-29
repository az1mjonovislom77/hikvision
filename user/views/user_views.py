from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from user.models import User
from user.serializers.user_serializers import UserCreateSerializer, UserDetailSerializer
from utils.base.views_base import PartialPutMixin


@extend_schema(tags=["User"])
class UserViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == ["retrieve"]:
            return UserDetailSerializer
        return UserCreateSerializer
