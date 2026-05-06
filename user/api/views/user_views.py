from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from utils.base.views_base import PartialPutMixin
from rest_framework.permissions import IsAuthenticated
from user.api.serializers.user_serializers import UserCreateSerializer, UserDetailSerializer
from user.selectors.user import users_queryset


@extend_schema(tags=["User"])
class UserViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = users_queryset()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == ["retrieve"]:
            return UserDetailSerializer
        return UserCreateSerializer
